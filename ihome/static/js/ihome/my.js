function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
function logout() {
    $.ajax({
        url: "/api/v1_0/session",
        type: "delete",
        dataType: "json",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        success: function (data) {
            if (0 == data.errno) {
                location.href = "/";
            }
        }
    })
}

$(document).ready(function () {


    $.ajax({
        url: "/api/v1_0/users/user_info",
        type: "get",
        dataType: "json",
        success: function (resp) {
            console.log(resp)
            if (0 == resp.errno) {
                $("#user-avatar").attr("src", resp.data.avatar_url)
                $("#user-mobile").html(resp.data.user_mobile)
                $("#user-name").html(resp.data.user_name)
            } else if (resp.errno == "4101") {
                location.href = "/"
            }
        }
    })
})