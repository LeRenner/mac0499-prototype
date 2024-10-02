///////////////////////////////////////////////
//////// Interface Updates ////////////////////
///////////////////////////////////////////////


let previousChatListHash = '';

async function generateChatList() {
    try {
        const messages = await getLatestMessages();

        console.log('Received messages: ' + JSON.stringify(messages));

        // Hash the messages content
        const messagesString = JSON.stringify(messages);
        const currentMessagesHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(messagesString));
        const currentMessagesHashHex = Array.from(new Uint8Array(currentMessagesHash)).map(b => b.toString(16).padStart(2, '0')).join('');

        // Check if the hash has changed
        if (currentMessagesHashHex === previousChatListHash) {
            console.log('No new messages, skipping update.');
            return;
        }

        // Update the previous hash
        previousChatListHash = currentMessagesHashHex;

        // check messages length
        if (messages.length === 0) {
            document.getElementById('senders').innerHTML = 'No message received yet...';
        } else {
            let chatList = '';

            messages.forEach(message => {
                const formattedTimestamp = convertTimestamp(message.timestamp);

                chatList += `
                    <div class="contact">
                        <p class="address">
                            ${message.sender}
                        </p>
                        <p class="message-bottom">
                            <span class="latest-message">${message.content}</span>
                            <span class="timestamp">${formattedTimestamp}</span>
                        </p>
                    </div><br/>
                `;
            });

            document.getElementById('senders').innerHTML = chatList;
        }
    } catch (error) {
        console.log('Error receiving messages: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving messages';
    }
}


let previousMessagesHash = '';

async function generateMessageList() {
    try {
        console.log(currentChatAddress);

        const messages = await getMessagesFromSender(currentChatAddress);

        console.log('Received messages: ' + JSON.stringify(messages));

        // Combine receivedMessages and sentMessages
        const allMessages = [...messages.receivedMessages, ...messages.sentMessages];

        // Sort messages chronologically by timestamp
        allMessages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        // Hash the messages content
        const messagesString = JSON.stringify(allMessages);
        const currentMessagesHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(messagesString));
        const currentMessagesHashHex = Array.from(new Uint8Array(currentMessagesHash)).map(b => b.toString(16).padStart(2, '0')).join('');

        // Check if the hash has changed
        if (currentMessagesHashHex === previousMessagesHash) {
            return;
        }

        // Update the previous hash
        previousMessagesHash = currentMessagesHashHex;

        // check messages length
        if (allMessages.length === 0) {
            document.getElementById('receivedMessages').innerHTML = 'No messages received yet...';
        } else {
            let chatList = '';

            allMessages.forEach(message => {
                const formattedTimestamp = convertTimestamp(message.timestamp);
                const messageClass = message.sender === currentChatAddress ? 'receivedMessage' : 'sentMessage';

                chatList += `
                    <div class="message ${messageClass}">
                        <p class="message-content">
                            ${message.content}
                        </p>
                        <p class="message-timestamp">
                            ${formattedTimestamp}
                        </p>
                    </div><br/>
                `;
            });

            document.getElementById('receivedMessages').innerHTML = chatList;

            // update sender-address with currentChatAddress
            document.getElementById('sender-address').innerHTML = currentChatAddress;
        }
    } catch (error) {
        console.log('Error receiving messages: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving messages';
    }
}


let previousFriendsHash = '';

async function getFriends() {
    try {
        const response = await fetch('/getFriends', {
            method: 'GET'
        });

        const data = await response.json();

        // Hash the friends content
        const friendsString = JSON.stringify(data.friends);
        const currentFriendsHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(friendsString));
        const currentFriendsHashHex = Array.from(new Uint8Array(currentFriendsHash)).map(b => b.toString(16).padStart(2, '0')).join('');

        // Check if the hash has changed
        if (currentFriendsHashHex === previousFriendsHash) {
            console.log('No new friends, skipping update.');
            return;
        }

        // Update the previous hash
        previousFriendsHash = currentFriendsHashHex;

        // check data.friends length
        if (data.friends.length === 0) {
            document.getElementById('friends').innerHTML = 'No friends yet...';
        } else {
            let friendsList = '';
            data.friends.forEach(friend => {
                friendsList += `
                    <div class="friend">
                        <p class="friend-name">
                            ${friend.name}
                        </p>
                        <p class="friend-address">
                            ${friend.address}
                        </p>
                    </div><br/>
                `;
            });

            document.getElementById('friends').innerHTML = friendsList;
        }
    } catch (error) {
        console.log('Error receiving friends: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving friends';
    }
}


async function showNewChat() {
    // switch between showing and hiding objects with class new-chat
    const newChat = document.querySelector('.new-chat');
    const newChatDisplay = newChat.style.display;
    newChat.style.display = newChatDisplay === 'block' ? 'none' : 'block';
}


async function addChat() {
    currentChatAddress = document.getElementById('new-chat-address').value;

    // clear the input field
    document.getElementById('new-chat-address').value = '';

    changeInterfaceState(1);
}


async function updateAddress() {
    // gets address from the server and updates the address element
    try {
        const response = await fetch('/getAddress', {
            method: 'GET'
        });

        const data = await response.json();

        document.getElementById('address').innerHTML = data.address;
    } catch (error) {
        console.log('Error receiving address: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving address';
    }
}