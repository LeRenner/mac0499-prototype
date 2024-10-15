let shouldRunUpdateFriendConnectionStatus = false;
async function updateFriendConnectionStatus() {
    if (shouldRunUpdateFriendConnectionStatus) {
        const connStatus = await request_getFriendConnectionStatus();

        console.log(connStatus.status);

        document.getElementById('friend-connection-status').innerHTML = " [" + connStatus.status + "]";
    }
}

async function changeFocusedFriend (friendAlias) {
    // address is the alias of the friend. Need to get the address from the alias
    const friends = await request_getFriends();
    let friendAddress = "";

    for (let i = 0; i < friends.length; i++) {
        if (friends[i].alias === friendAlias) {
            friendAddress = friends[i].address;
            break;
        }
    }

    await request_changeFocusedFriend(friendAddress);
}



// request_changeFocusedFriend
// request_getFriendConnectionStatus