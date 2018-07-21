function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $.get("/api/v1_0/areas", function (resp) {
        if (resp.errno == 0) {
            area_html = template("area-temp", {areas: resp.data.areas});
            $("#area-id").html(area_html)
        } else {
            alert(resp.errmsg)
        }
    })

    $("#form-house-info").submit(function (e) {
        e.preventDefault();

        var house_data = {}
        $(this).serializeArray().map(function (x) {
            house_data[x.name] = x.value
        })
        house_data["facility"] = []
        $(":checked[name=facility]").map(function (x) {
            house_data["facility"].push(x)
        })

        $.ajax({
            url: "/api/v1_0/house/info",
            data: JSON.stringify(house_data),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    $("#form-house-info").hide()
                    $("#form-house-image").show()
                    $("#house-id").val(resp.data.house_id)

                } else if (resp.errno == 4103) {
                    $(".error-msg").show()
                } else if (resp.errno == 4101) {
                    location.href = "/login.html"
                } else {
                    alert(resp.errmsg)
                }
            }
        })

    })

    $("#form-house-image").submit(function (e) {
        e.preventDefault();

        $(this).ajaxSubmit({
            url: "/api/v1_0/house/image",
            type: "POST",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    // 保存图片成功
                    $(".house-image-cons").append('<img src="' + resp.data.house_image_url + '">');

                } else if (resp.errno == 4101) {
                    location.href = "/login.html"
                } else {
                    alert(resp.errmsg)
                }
            }
        })

    })

    // $('.popup_con').fadeIn('fast');
    // $('.popup_con').fadeOut('fast');
})