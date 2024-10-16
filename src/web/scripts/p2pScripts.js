let shouldRunUpdateFriendConnectionStatus = false;
async function updateFriendConnectionStatus() {
    if (shouldRunUpdateFriendConnectionStatus) {
        const connStatus = await request_getFriendConnectionStatus();

        console.log(connStatus.status);

        document.getElementById('friend-connection-status').innerHTML = " [" + connStatus.status + "]";
    }
}

async function changeFocusedFriend (friendAlias) {
    const friendAddress = await addressFromAlias(friendAlias);
    await request_changeFocusedFriend(friendAddress);
}



// request_changeFocusedFriend
// request_getFriendConnectionStatus