import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import pandas as pd
import random
import json
from datetime import datetime, timedelta

app = Flask(__name__)
socketio = SocketIO(app)

# Constants
WORLD_SIZE = (100, 100)
INITIAL_POPULATION = 10
TIME_STEP = timedelta(days=365)  # 1 year per update
INITIAL_DATE = datetime(1, 1, 1)  # Start from year 1

# Ensure progress directory exists
progress_dir = 'progress'
os.makedirs(progress_dir, exist_ok=True)

# Character classes
class Character:
    def __init__(self, char_type, health, age, position, birth_date):
        self.char_type = char_type
        self.health = health
        self.age = age
        self.position = position
        self.birth_date = birth_date
    
    def move(self, world_size):
        dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        new_x = (self.position[0] + dx) % world_size[0]
        new_y = (self.position[1] + dy) % world_size[1]
        self.position = (new_x, new_y)

    def age_character(self):
        self.age += 1
        if self.age > 80:
            self.health -= 10

class Human(Character):
    def __init__(self, health, age, position, birth_date, knowledge):
        super().__init__('human', health, age, position, birth_date)
        self.knowledge = knowledge
    
    def reproduce(self, current_date):
        if self.age > 18 and self.health > 50:
            return Human(100, 0, self.position, current_date, 0)

class Animal(Character):
    def __init__(self, health, age, position, birth_date):
        super().__init__('animal', health, age, position, birth_date)
    
    def reproduce(self, current_date):
        if self.age > 2 and self.health > 20:
            return Animal(100, 0, self.position, current_date)

class Insect(Character):
    def __init__(self, health, age, position, birth_date):
        super().__init__('insect', health, age, position, birth_date)
    
    def reproduce(self, current_date):
        if self.age > 1 and self.health > 10:
            return Insect(50, 0, self.position, current_date)

# Create initial characters
characters = []
current_date = INITIAL_DATE
for _ in range(INITIAL_POPULATION):
    char_type = random.choice(['human', 'animal', 'insect'])
    if char_type == 'human':
        characters.append(Human(100, 20, (random.randint(0, 99), random.randint(0, 99)), current_date, 0))
    elif char_type == 'animal':
        characters.append(Animal(100, 10, (random.randint(0, 99), random.randint(0, 99)), current_date))
    else:
        characters.append(Insect(50, 1, (random.randint(0, 99), random.randint(0, 99)), current_date))

# Helper function to save state
def save_state(characters, date):
    state = [{
        'type': char.char_type, 
        'health': char.health, 
        'age': char.age, 
        'position': char.position,
        'birth_date': char.birth_date.isoformat(),
        'knowledge': getattr(char, 'knowledge', None)
    } for char in characters]
    
    json_filename = os.path.join(progress_dir, f'state_{date.isoformat()}.json')
    txt_filename = os.path.join(progress_dir, f'state_{date.isoformat()}.txt')

    with open(json_filename, 'w') as json_file:
        json.dump(state, json_file, indent=4)

    with open(txt_filename, 'w') as txt_file:
        for char in state:
            txt_file.write(f"{char}\n")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# SocketIO events
@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

@socketio.on('request_update')
def handle_update():
    global current_date
    new_characters = []
    for character in characters:
        character.move(WORLD_SIZE)
        character.age_character()
        if isinstance(character, Human):
            offspring = character.reproduce(current_date)
            if offspring:
                new_characters.append(offspring)
        elif isinstance(character, Animal):
            offspring = character.reproduce(current_date)
            if offspring:
                new_characters.append(offspring)
        elif isinstance(character, Insect):
            offspring = character.reproduce(current_date)
            if offspring:
                new_characters.append(offspring)

    characters.extend(new_characters)
    current_date += TIME_STEP
    
    data = [{
        'type': char.char_type, 
        'health': char.health, 
        'age': char.age, 
        'position': char.position, 
        'birth_date': char.birth_date.isoformat(), 
        'knowledge': getattr(char, 'knowledge', None)
    } for char in characters]
    
    # Save state periodically
    save_state(characters, current_date)
    
    emit('update', {'date': current_date.isoformat(), 'characters': data})

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    port = 5000
    print(f"Simulation running at http://{ip_address}:{port}")
    socketio.run(app, host='0.0.0.0', port=port)
