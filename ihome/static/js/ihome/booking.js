function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery() {
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function (result, item) {
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg() {
    $('.popup_con').fadeIn('fast', function () {
        setTimeout(function () {
            $('.popup_con').fadeOut('fast', function () {
            });
        }, 1000)
    });
}

$(document).ready(function () {
    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function () {
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg();
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd) / (1000 * 3600 * 24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共" + days + "晚)");
        }
    });

    var house_id = decodeQuery()["hid"]

    $.get("/api/v1_0/order/house", {house_id: house_id}, function (resp) {
        if (resp.errno == 0) {
            $(".house-info>img").attr("src",resp.data.img_url)
            $(".house-text>h3").html(resp.data.title)
            $(".house-text>p>span").html((resp.data.price/100).toFixed(2))
        }else if(resp.errno == 4101){
            location.href = "/login.html"
        } else {
            alert(resp.errmsg)
        }
    })


    // 提交订单
    $(".submit-btn").click(function () {

        var start_date = $("#start-date").val()
        var end_date = $("#end-date").val()
        var req_data = {
            start_date: start_date,
            end_date: end_date,
            house_id: house_id
        }
        $.ajax({
            url: "/api/v1_0/order",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(req_data),
            dataType: "json",
            // 自定义请求头
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    location.href = "/orders.html"
                } else if (resp.errno == 4101) {
                    location.href = "/login.html"
                } else {
                    alert(resp.errmsg)
                }
            }


        })


    })
})
