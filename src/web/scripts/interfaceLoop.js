// 0 for senders, 1 for chat
let interfaceState = 0;
let currentChatAddress = '';


// every second get messages and update the UI
async function updateUI() {
    if (interfaceState === 0) {
        generateChatList();
    } else if (interfaceState === 1) {
        generateMessageList();
        await updateFriendConnectionStatus();
    } else if (interfaceState === 2) {
        updateFriends();
    }
}


function changeInterfaceState(newState) {
    interfaceState = newState;
    
    if (newState === 0) {
        request_changeFocusedFriend('0');
        shouldRunUpdateFriendConnectionStatus = false;
        document.getElementById('senderList').style.display = 'block';
        document.getElementById('chat').style.display = 'none';
        document.getElementById('friends').style.display = 'none';
    } else if (newState === 1) {
        document.getElementById('senderList').style.display = 'none';
        document.getElementById('chat').style.display = 'block';
        document.getElementById('friends').style.display = 'none';
    } else if (newState === 2) {
        request_changeFocusedFriend('0');
        shouldRunUpdateFriendConnectionStatus = false;
        document.getElementById('senderList').style.display = 'none';
        document.getElementById('chat').style.display = 'none';
        document.getElementById('friends').style.display = 'block';
    }

    updateUI();
}


// when clicking on id address, copy it to clipboard and append "(copied)" for one second
document.getElementById('address').addEventListener('click', function() {
    const addressElement = document.getElementById('address');
    const address = addressElement.innerText;
    navigator.clipboard.writeText(address);

    const originalText = addressElement.innerHTML;
    addressElement.innerHTML += ' (copied)';
    console.log('address copied');
    setTimeout(() => {
        addressElement.innerHTML = originalText;
    }, 1000);
});


var sendMessage = document.getElementById("message");
sendMessage.addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {
        event.preventDefault();
        document.getElementById("botaodeenviaramensagemporqueodanielmandou").click();
    }
})


// when clicking on anything with the class contact, set address and show chat
document.getElementById('senders').addEventListener('click', async function(event) {
    if (event.target.classList.contains('contact') || 
        event.target.classList.contains('message-bottom') || 
        event.target.classList.contains('latest-message') || 
        event.target.classList.contains('timestamp') || 
        event.target.classList.contains('address')) {
        currentChatAddress = event.target.closest('.contact').querySelector('.address').innerText;

        // if current chat address starts and ends with []
        if (currentChatAddress.startsWith('[') && currentChatAddress.endsWith(']')) {
            // start running the update friend connection status loop
            await changeFocusedFriend(currentChatAddress.slice(1, -1));
            shouldRunUpdateFriendConnectionStatus = true;

            currentChatAddress = await addressFromAlias(currentChatAddress);
            console.log('Clicked on alias: ' + currentChatAddress);
        }

        console.log('Clicked on address: ' + currentChatAddress);
        changeInterfaceState(1);
    }
});


// then clicking on item with ID friends-tab, show friends
document.getElementById('friends-tab').addEventListener('click', function() {
    changeInterfaceState(2);
});


// when clicking on item with ID senders-tab, show senders
document.getElementById('chats-tab').addEventListener('click', function() {
    previousChatListHash = '';
    changeInterfaceState(0);
});


// when on chat an esc is pressed, go back to senders
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && interfaceState === 1) {
        changeInterfaceState(0);
    }
});


setInterval(updateUI, 1000);

// hide chat and show senders
document.getElementById('senders').style.display = 'block';
document.getElementById('chat').style.display = 'none';
document.getElementById('friends').style.display = 'none';
interfaceState = 0;

updateAddress();