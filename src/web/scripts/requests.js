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

        return data.messages;
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
async function sendMessage(messageContent, address) {
    try {
        const response = await fetch('/sendMessage', {
            method: 'POST',
            body: JSON.stringify({
                address: address,
                message: messageContent
            })
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

// returns list of friends
async function getFriends() {
    try {
        const response = await fetch('/getFriends', {
            method: 'GET'
        });

        const data = await response.json();

        return data.friends;
    } catch (error) {
        return {};
    }
}


///////////////////////////////////////////////
//////// Buttons //////////////////////////////
///////////////////////////////////////////////

async function sendMessage() {
    const messageCont = document.getElementById('message').value;

    document.getElementById('status').innerHTML = 'Sending message...';

    try {
        const result = await sendMessage(messageCont, currentChatAddress);

        if (result.success) {
            document.getElementById('status').innerHTML = 'Message sent successfully!';
            document.getElementById('message').value = '';
        } else {
            document.getElementById('status').innerHTML = 'Error sending message';
        }
    } catch (error) {
        console.log('Error sending message: ' + error.message);
        document.getElementById('status').innerHTML = 'Error sending message';
    }
}