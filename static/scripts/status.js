var httpObject = new XMLHttpRequest();
var origin = window.location.origin;

var doorStatus = null;
var lockStatus = null;
var autolockEnabled = null;
var lightStatus = null;
var temperature = null;
var messageContent = null;

function setDoorString(door, lock) {
    var element = document.getElementById("proplist-lockstatus");

    if((door != null) && (lock != null)) {
        
        if(door == true) {
            if(lock == true) {
                element.innerHTML = "closed and locked";
            } else if(lock == false) {
                element.innerHTML = "closed but unlocked";
            } else {
                element.innerHTML = "unknown error";
            }
        } else if(door == false) {
            if(lock == true) {
                element.innerHTML = "open but locked";
            } else if(lock == false) {
                element.innerHTML = "open and unlocked";
            } else {
                element.innerHTML = "unknown error";
            }
        }
    }
}

function setAutolockString(enabled) {
    var element = document.getElementById("proplist-autolock");

    if(enabled) {
        element.innerHTML = "Auto-lock enabled";
    } else {
        element.innerHTML = "Auto-lock disabled";
    }
}

function setMessage(message) {
    var element = document.getElementById("motd-text");

    if(messageContent == null) {
        element.innerHTML = "error - null value or message not set";
    } else {
        element.innerHTML = message;
    }
}

httpObject.onreadystatechange = function() {
    
    if(this.readyState == 4 && this.status == 200) {
        
        var parsed = JSON.parse(this.responseText);
        
        if(parsed["door-status"] != null) {
            doorStatus = parsed["door-status"];
        } else {
            lockStatus = null;
        }

        if(parsed["lock-status"] != null) {
            lockStatus = parsed["lock-status"];
        } else {
            lockStatus = null;
        }

        if(parsed["autolock-enabled"] != null) {
            autolockEnabled = parsed["autolock-enabled"];
        } else {
            autolockEnabled = null;
        }

        if(parsed["motd"] != null) {
            messageContent = parsed["motd"];
        } else {
            messageContent = null;
        }

        if(parsed["light-status"] != null) {
            lightStatus = parsed["light-status"];
        } else {
            lightStatus = null;
        }

        if(parsed["temperature"] != null) {
            temperature = parsed["temperature"];
        } else {
            temperature = null;
        }

        setDoorString(doorStatus, lockStatus);
        setAutolockString(autolockEnabled);
        setMessage(messageContent);
    }
}

function fetchAJAJ() {
    httpObject.open("GET", origin+"/infodigest", true);
    httpObject.send();
}

window.setInterval(fetchAJAJ, 1000);
