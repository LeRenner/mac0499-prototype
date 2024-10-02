///////////////////////////////////////////////
//////// Interface Updates ////////////////////
///////////////////////////////////////////////


let previousChatListHash = '';

async function generateChatList() {
    try {
        const messages = await getLatestMessages();

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
        const messages = await getMessagesFromSender(currentChatAddress);

        console.log('Messages from ' + currentChatAddress + ': ' + JSON.stringify(messages));

        // Hash the messages content
        const messagesString = JSON.stringify(messages);
        const currentMessagesHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(messagesString));
        const currentMessagesHashHex = Array.from(new Uint8Array(currentMessagesHash)).map(b => b.toString(16).padStart(2, '0')).join('');

        // Check if the hash has changed
        if (currentMessagesHashHex === previousMessagesHash) {
            return;
        }

        // Update the previous hash
        previousMessagesHash = currentMessagesHashHex;

        // check messages length
        if (messages.length === 0) {
            document.getElementById('chat').innerHTML = 'No messages received yet...';
        } else {
            let chatList = '';

            messages.forEach(message => {
                const formattedTimestamp = convertTimestamp(message.timestamp);

                chatList += `
                    <div class="message">
                        <p class="message-content">
                            ${message.content}
                        </p>
                        <p class="message-timestamp">
                            ${formattedTimestamp}
                        </p>
                    </div><br/>
                `;
            });

            document.getElementById('chat').innerHTML = chatList;
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