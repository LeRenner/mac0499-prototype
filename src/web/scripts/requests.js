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

    try {
        const result = await requestSendMessage(messageCont, currentChatAddress);

        if (result.success) {
            document.getElementById('message').value = '';
        } else {
        }
    } catch (error) {
        console.log('Error sending message: ' + error.message);
    }
}