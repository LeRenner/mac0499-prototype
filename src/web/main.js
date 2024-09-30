async function sendMessage() {
    const address = document.getElementById('address').value;
    const message = document.getElementById('message').value;

    const data = {
        address: address,
        message: message
    };

    const packagedData = JSON.stringify(data);

    console.log('Sending message: ' + packagedData);

    try {
        const formData = new FormData();
        formData.append('message', packagedData);

        const response = await fetch('/sendMessage', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        alert("Message sent successfully! Response: " + JSON.stringify(result));
    } catch (error) {
        console.log('Error sending message: ' + error.message);
    }
}

async function receiveMessages() {
    try {
        const response = await fetch('/getMessages', {
            method: 'GET'
        });

        const data = await response.json();

        console.log('Received messages: ' + JSON.stringify(data));

        // check data.messages length
        if (data.messages.length === 0) {
            document.getElementById('messages').innerHTML = 'No message received yet...';
        } else {
            let messages = '';
            data.messages.forEach(message => {
                messages += 'From: ' + message.sender + ' - Message: ' + message.content + '<br>';
            });

            document.getElementById('receivedMessages').innerHTML = messages;
        }
    } catch (error) {
        console.log('Error receiving message: ' + error.message);
    }
}

// every second get /receive