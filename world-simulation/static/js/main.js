document.addEventListener("DOMContentLoaded", function() {
    const canvas = document.getElementById("world");
    const ctx = canvas.getContext("2d");
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    let animationFrameId;

    function drawWorld(characters) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        characters.forEach(char => {
            if (char.type === 'human') {
                ctx.fillStyle = 'blue';
            } else if (char.type === 'animal') {
                ctx.fillStyle = 'green';
            } else if (char.type === 'insect') {
                ctx.fillStyle = 'red';
            }
            ctx.fillRect(char.position[0] * 5, char.position[1] * 5, 5, 5);
        });
    }

    socket.on('update', function(data) {
        drawWorld(data.characters);
    });

    document.getElementById("start").addEventListener("click", function() {
        if (!animationFrameId) {
            function update() {
                socket.emit('request_update');
                animationFrameId = requestAnimationFrame(update);
            }
            update();
        }
    });

    document.getElementById("pause").addEventListener("click", function() {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
    });
});
