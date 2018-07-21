function hrefBack() {
    history.go(-1);
}


function decodeQuery() {
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function (result, item) {
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function () {
    var queryData = decodeQuery()
    var house_id = queryData["id"]
    $.get("/api/v1_0/house/detail", {house_id: house_id}, function (resp) {
        if (resp.errno == 0) {
            houses_info_html = template("house-temp", {house: resp.data.house})
            $(".container").html(houses_info_html)


            if (resp.data.user_id != resp.data.house.user_id) {
                $(".book-house").attr("href", "/booking.html?hid="+resp.data.house.hid);
                $(".book-house").show();

            }
            var mySwiper = new Swiper('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            })
        } else {
            alert(resp.errmsg)
        }
    }, "json")
    


})