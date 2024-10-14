///////////////////////////////////////////////
//////// Requests to the server //////////////
///////////////////////////////////////////////


// returns list of messages from specific sender
async function getMessagesFromSender(sender) {
    try {
        const response = await fetch('/getMessagesFromSender', {
            method: 'POST',
            body: sender
        });

        const data = await response.json();

        return data;
    } catch (error) {
        return {};
    }
}


// returns list with the latest message from each sender
async function getLatestMessages() {
    try {
        const response = await fetch('/getLatestMessages', {
            method: 'GET'
        });

        const data = await response.json();

        return data.messages;
    } catch (error) {
        return {};
    }
}


// returns list of messages from specific sender
async function requestSendMessage(messageContent, address) {
    try {
        const response = await fetch('/sendMessage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: address,
                message: messageContent
            })
        });

        const data = await response.json();

        console.log(data);

        return data;
    } catch (error) {
        return {"error": "Local request failed"};
    }
}


// returns list with the latest message from each sender
async function getLatestMessages() {
    try {
        const response = await fetch('/getLatestMessages', {
            method: 'GET'
        });

        const data = await response.json();

        return data.messages;
    } catch (error) {
        return {};
    }
}

// returns list of friends
async function getFriends() {
    try {
        const response = await fetch('/getFriends', {
            method: 'GET'
        });

        const data = await response.json();

        return data;
    } catch (error) {
        return {};
    }
}

// adds request for new friend
async function addFriend() {
    const address = document.getElementById('new-friend-address').value;
    const alias = document.getElementById('new-friend').value;

    try {
        const response = await fetch('/addFriend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: address,
                alias: alias
            })
        });

        const data = await response.json();

        console.log(data);

        return data;
    } catch (error) {
        return {};
    }
}

// removes friend
async function removeFriend() {
    const alias = document.getElementById('remove-friend').value;

    try {
        const response = await fetch('/removeFriend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alias: alias
            })
        });

        const data = await response.json();

        console.log(data);

        return data;
    } catch (error) {
        return {};
    }
}

// starts new chat with friend
async function startChat(address) {
    try {
        const response = await fetch('/startChat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: address
            })
        });

        const data = await response.json();

        if (data.error) {
            return false;
        }

        return true
    } catch (error) {
        return false;
    }
}


///////////////////////////////////////////////
//////// Buttons //////////////////////////////
///////////////////////////////////////////////

async function sendMessage() {
    document.querySelector('.sending-message').style.display = 'block';
    document.querySelector('.message-sent').style.display = 'none';
    document.querySelector('.message-error').style.display = 'none';

    const messageCont = document.getElementById('message').value;

    try {
        const result = await requestSendMessage(messageCont, currentChatAddress);

        if (result.message == "processing") {
            document.querySelector('.sending-message').style.display = 'block';
            document.querySelector('.sending-message').innerHTML = 'First message! Estabilishing first contact handshake...';

            result = await requestSendMessage(messageCont, currentChatAddress);
        }

        if (!result.error) {
            document.querySelector('.sending-message').innerHTML = 'Sending message...';
            document.querySelector('.sending-message').style.display = 'none';
            document.querySelector('.message-sent').style.display = 'block';

            setTimeout(() => {
                document.querySelector('.message-sent').style.display = 'none';
            }, 3000);

            document.getElementById('message').value = '';
        } else {
            document.querySelector('.message-error').textContent = result.error;

            document.querySelector('.sending-message').style.display = 'none';
            document.querySelector('.message-error').style.display = 'block';

            setTimeout(() => {
                document.querySelector('.message-error').style.display = 'none';
            }, 10000);
        }
    } catch (error) {
        console.log('Error sending message: ' + error.message);
    }
}