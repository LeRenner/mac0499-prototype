// converts unix timestamp to human readable date
function convertTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const formattedDate = isToday ? 'Today' : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    const formattedTime = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    return `${formattedDate} ${formattedTime}`;
}

async function addressIsFriend(address) {
    const friends = await request_getFriends();
    return friends.some(friend => friend.address === address);
}

async function substituteAlias(address) {
    const friends = await request_getFriends();
    let response = address;

    for (let i = 0; i < friends.length; i++) {
        if (friends[i].address === address) {
            response = "[" + friends[i].alias + "]";
            break;
        }
    }

    return response;
}

async function addressFromAlias(alias) {
    response = alias;
    if (alias.startsWith('[') && alias.endsWith(']')) {
        response = alias.slice(1, -1);
    }

    const friends = await request_getFriends();
    for (let i = 0; i < friends.length; i++) {

        if (friends[i].alias == response) {
            response = friends[i].address;
            break;
        }
    }

    return response;
}