// converts unix timestamp to human readable date
function convertTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const formattedDate = isToday ? 'Today' : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    const formattedTime = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    return `${formattedDate} ${formattedTime}`;
}