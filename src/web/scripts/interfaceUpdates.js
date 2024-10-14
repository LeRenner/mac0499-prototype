///////////////////////////////////////////////
//////// Interface Updates ////////////////////
///////////////////////////////////////////////


let previousChatListHash = '';

async function generateChatList() {
    try {
        const messages = await getLatestMessages();
        const friends = await getFriends();

        // Create a map of addresses to aliases
        const addressToAlias = new Map();
        friends.forEach(friend => {
            addressToAlias.set(friend.address, friend.alias);
        });

        // Hash the messages content
        const messagesString = JSON.stringify(messages);
        const currentMessagesHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(messagesString));
        const currentMessagesHashHex = Array.from(new Uint8Array(currentMessagesHash)).map(b => b.toString(16).padStart(2, '0')).join('');

        // Check if the hash has changed
        if (currentMessagesHashHex === previousChatListHash) {
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
                let senderAlias = addressToAlias.get(message.sender) || message.sender;
                if (addressToAlias.has(message.sender)) {
                    senderAlias = `[${senderAlias}]`;
                }

                chatList += `
                    <div class="contact">
                        <p class="address">
                            ${senderAlias}
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
    }
}


let previousMessagesHash = '';

async function generateMessageList() {
    console.log('Generating message list...');
    try {
        const messages = await getMessagesFromSender(currentChatAddress);

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

            if (message.sender === currentChatAddress) {
                chatList += `
                <div class="message-container">
                    <div class="message ${messageClass}">
                    <p class="message-content">
                        ${message.content}
                    </p>
                    <p class="message-timestamp">
                        ${formattedTimestamp}
                    </p>
                    </div>
                    <div class="spacer"></div>
                </div>
                <div class="messageSpacer"></div>
                `;
            } else {
                chatList += `
                <div class="message-container">
                    <div class="spacer"></div>
                    <div class="message ${messageClass}">
                    <p class="message-content">
                        ${message.content}
                    </p>
                    <p class="message-timestamp">
                        ${formattedTimestamp}
                    </p>
                    </div>
                </div>
                <div class="messageSpacer"></div>
                `;
            }
            });

            document.getElementById('receivedMessages').innerHTML = chatList;

            // Scroll to the end of the div with ID receivedMessages
            const receivedMessagesDiv = document.getElementById('receivedMessages');
            receivedMessagesDiv.scrollTop = receivedMessagesDiv.scrollHeight;
        }
        // update sender-address with currentChatAddress
        let senderAlias = currentChatAddress;
        const friends = await getFriends();
        friends.forEach(friend => {
            if (friend.address === currentChatAddress) {
                senderAlias = friend.alias;
            }
        });
        console.log(senderAlias);
        document.getElementById('sender-address').innerHTML = senderAlias;
    } catch (error) {
        console.log('Error receiving messages: ' + error.message);
    }
}


let previousFriendsHash = '';

async function updateFriends() {
    try {
        const response = await fetch('/getFriends', {
            method: 'GET'
        });

        const data = await response.json();

        console.log(data);

        // Hash the friends content
        const friendsString = JSON.stringify(data);
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
        if (data.length === 0) {
            document.getElementById('friendsList').innerHTML = 'No friends yet...';
        } else {
            let friendsList = '<hr/>';
            data.forEach(friend => {
                friendsList += `
                    <div class="friend">
                        <p class="friend-name">
                            ${friend.alias}
                        </p>
                        <p class="friend-address">
                            ${friend.address}
                        </p>
                    </div><hr/>
                `;
            });

            document.getElementById('friendsList').innerHTML = friendsList;
        }
    } catch (error) {
        console.log('Error receiving friends: ' + error.message);
    }
}


async function showNewChat() {
    // switch between showing and hiding objects with class new-chat
    const newChat = document.querySelector('.new-chat');
    const newChatDisplay = newChat.style.display;
    newChat.style.display = newChatDisplay === 'block' ? 'none' : 'block';
}


async function showNewFriend() {
    // switch between showing and hiding objects with class friends
    const newFriend = document.querySelector('.new-friend');
    const newFriendDisplay = newFriend.style.display;
    newFriend.style.display = newFriendDisplay === 'block' ? 'none' : 'block';

}


async function addChat() {
    currentChatAddress = document.getElementById('new-chat-address').value;

    // check if is tor address (length of 56 random characters followed by .onion)
    // first, separate the address by the . character
    const addressParts = currentChatAddress.split('.');
    // then, check if the first part has 56 characters
    if (addressParts[0].length !== 56 || addressParts[1] !== 'onion') {
        document.querySelector('.add-friend-status').innerHTML = 'Invalid address!';
        document.querySelector('.add-friend-status').style.display = 'block';

        setTimeout(() => {
            document.querySelector('.add-friend-status').style.display = 'none';
        }, 3000);
        return;
    }

    document.querySelector('.add-friend-status').innerHTML = 'Getting user public key... (will try for up to 45s)';
    document.querySelector('.add-friend-status').style.display = 'block';


    const chatStarted = await startChat(currentChatAddress);

    if (!chatStarted) {
        document.querySelector('.add-friend-status').innerHTML = "Couldn't get friend public key. Check if they are online!";
        return;
    }

    // clear the input field
    document.getElementById('new-chat-address').value = '';

    document.querySelector('.add-friend-status').innerHTML = 'Successfully retrieved public key!';

    setTimeout(() => {
        changeInterfaceState(1);
    }, 1000);
}


async function updateAddress() {
    // gets address from the server and updates the address element
    try {
        const response = await fetch('/getAddress', {
            method: 'GET'
        });
        
        const data = await response.json();

        console.log(data);

        document.getElementById('address').innerHTML = data.address;
    }
    catch (error) {
        console.log('Error receiving address: ' + error.message);
    }
}