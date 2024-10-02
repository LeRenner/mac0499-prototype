// 0 for senders, 1 for chat
let interfaceState = 0;
let currentChatAddress = '';


// every second get messages and update the UI
function updateUI() {
    if (interfaceState === 0) {
        generateChatList();
    } else if (interfaceState === 1) {
        generateMessageList();
    } else if (interfaceState === 2) {
        getFriends();
    }
}


function changeInterfaceState(newState) {
    interfaceState = newState;
    
    if (newState === 0) {
        document.getElementById('senders').style.display = 'block';
        document.getElementById('chat').style.display = 'none';
        document.getElementById('friends').style.display = 'none';
    } else if (newState === 1) {
        document.getElementById('senders').style.display = 'none';
        document.getElementById('chat').style.display = 'block';
        document.getElementById('friends').style.display = 'none';
    } else if (newState === 2) {
        document.getElementById('senders').style.display = 'none';
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
        changeInterfaceState(1);
    }
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