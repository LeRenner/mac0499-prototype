async function sendMessage() {
    const addressCont = document.getElementById('destAddress').value;
    const messageCont = document.getElementById('message').value;

    document.getElementById('status').innerHTML = 'Sending message...';

    const data = {
        address: addressCont,
        message: messageCont
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
        document.getElementById('status').innerHTML = 'Message sent successfully!';
    } catch (error) {
        console.log('Error sending message: ' + error.message);
        document.getElementById('status').innerHTML = 'Error sending message';
    }
}


async function generateChatList() {
    try {
        const response = await fetch('/getMessages', {
            method: 'GET'
        });

        const data = await response.json();

        // check data.messages length
        if (data.messages.length === 0) {
            document.getElementById('senders').innerHTML = 'No message received yet...';
        } else {
            let messages = '';
            let contacts = {};

            data.messages.forEach(message => {
                const formattedTimestamp = convertTimestamp(message.timestamp);

                if (!contacts[message.sender]) {
                    contacts[message.sender] = {
                        address: message.sender,
                        latestMessage: message.content,
                        timestamp: formattedTimestamp
                    };
                } else if (message.timestamp > new Date(contacts[message.sender].timestamp).getTime() / 1000) {
                    contacts[message.sender].latestMessage = message.content;
                    contacts[message.sender].timestamp = formattedTimestamp;
                }
            });

            for (const sender in contacts) {
                messages += `
                    <div class="contact">
                        <p class="address">
                            ${contacts[sender].address}
                        </p>
                        <p class="message-bottom">
                            <span class="latest-message">${contacts[sender].latestMessage}</span>
                            <span class="timestamp">${contacts[sender].timestamp}</span>
                        </p>
                    </div><br/>
                `;
            }

            document.getElementById('senders').innerHTML = messages;
        }
    }
    catch (error) {
        console.log('Error receiving message: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving messages';
    }
}


async function receiveMessages() {
    try {
        const response = await fetch('/getMessages', {
            method: 'GET'
        });

        const data = await response.json();

        // check data.messages length
        if (data.messages.length === 0) {
            document.getElementById('receivedMessages').innerHTML = 'No message received yet...';
        } else {
            let messages = '';
            data.messages.forEach(message => {
                messages += 'From: ' + message.sender + ' - Message: ' + message.content + '<br><br>';
            });

            document.getElementById('receivedMessages').innerHTML = messages;
        }

        document.getElementById('address').innerHTML = data.address;
    } catch (error) {
        console.log('Error receiving message: ' + error.message);
        document.getElementById('status').innerHTML = 'Error receiving messages';
    }

    if (document.getElementById('status').innerHTML == "NOT STARTED") {
        document.getElementById('status').innerHTML = 'Synced';
    }
}


// converts unix timestamp to human readable date
// 1727822058 -> 10 Nov 16:04
// uses current timezone
// if today, replace date with "Today"
function convertTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const formattedDate = isToday ? 'Today' : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    const formattedTime = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    return `${formattedDate} ${formattedTime}`;
}




// 0 for senders, 1 for chat
let interfaceState = 0;
let currentChatAddress = '';


// every second get messages and update the UI
function updateUI() {
    if (interfaceState === 0) {
        generateChatList();
    } else {
        receiveMessages();
    }
}


// when clicking on id address, copy it to clipboard and append "(copied)" for one second
document.getElementById('address').addEventListener('click', function() {
    const addressElement = document.getElementById('address');
    const address = addressElement.innerText;
    navigator.clipboard.writeText(address);
    document.getElementById('status').innerHTML = 'Address copied to clipboard!';

    const originalText = addressElement.innerHTML;
    addressElement.innerHTML += ' (copied)';
    setTimeout(() => {
        addressElement.innerHTML = originalText;
    }, 1000);
});

// when clicking on anything with the class contact, set address and show chat
document.getElementById('senders').addEventListener('click', function(event) {
    if (event.target.classList.contains('contact') || 
        event.target.classList.contains('message-bottom') || 
        event.target.classList.contains('latest-message') || 
        event.target.classList.contains('timestamp') || 
        event.target.classList.contains('address')) {
        currentChatAddress = event.target.closest('.contact').querySelector('.address').innerText;
        document.getElementById('senders').style.display = 'none';
        document.getElementById('chat').style.display = 'block';
        interfaceState = 1;
    }
});



// when on chat an esc is pressed, go back to senders
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && interfaceState === 1) {
        document.getElementById('senders').style.display = 'block';
        document.getElementById('chat').style.display = 'none';
        interfaceState = 0;
    }
});

setInterval(updateUI, 1000);

// hide chat and show senders
document.getElementById('senders').style.display = 'block';
document.getElementById('chat').style.display = 'none';