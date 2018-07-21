$(document).ready(function () {
    $("#houses-list").hide()
    $(".auth-warn").hide()
    $.get("/api/v1_0/houses/list", function (resp) {
        if (resp.errno == 4002) {
            $(".auth-warn").show();

        } else if (resp.errno == 0) {
            $("#houses-list").show();
            houses_html = template("houses-temp", {houses: resp.data.houses});
            $("#houses-list").html(houses_html)


        } else if (resp.errno == 4101) {
            location.href = "/login.html"
        }

    }, "json")

})


