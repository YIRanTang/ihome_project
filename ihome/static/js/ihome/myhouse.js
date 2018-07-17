$(document).ready(function () {
    $.get("/api/v1_0/houses/list", function (resp) {
        if (resp.errno == 4002) {
            $(".auth-warn").show();
            $("#houses-list").hide()
        } else if (resp.errno == 0) {
            $("#houses-list").show();
            $(".auth-warn").hide()
        } else if (resp.errno == 4101) {
            location.href = "/login.html"
        }

    }, "json")

})


