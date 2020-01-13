jQuery('.dropdown-menu').click(function (e) {
    e.stopPropagation();
});

var prevVal = '';
var addrPattern = new RegExp(/[a-zA-Z0-9\b]$/);
var namePattern = new RegExp(/[a-zA-Z0-9\b_-]$/);

function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

$(document).ready(function () {
    $("#searchBar").on("keyup", async function () {
        var original = $(this).val();
        var value = original.toLowerCase();
        var vm = angular.element($('body')).scope();

        if (value == prevVal) return;

        prevVal = value;

        if (value === "") {
            resetSideBar();
            vm.$apply(`basic.tempAddr={addr:'',url:''}`);
            return;
        }

        var categories = {};
        var exists = false;
        $("#accordion .addr").filter(function () {
            let isValid = ($(this).text().toLowerCase().indexOf(value) > -1 || $(this).attr("data-addy").toLowerCase() === value);
            if (isValid) {
                categories[$(this).parent().parent().attr('id')] = true;
                exists = true;
            }
            $(this).toggle(isValid);
        });

        if (Object.keys(categories).length == 2 && categories['Home']) {
            categories['Home'] = false;
        } else if (Object.keys(categories).length > 2) {
            categories = {
                'Home': true
            }
        }

        $("#accordion .category").filter(function () {
            let toggle = categories[$(this).attr('name')] === true;

            if (toggle) {
                $('#' + $(this).attr('name')).collapse('show');
            }

            $(this).toggle(toggle);
        });

        /*
        if (Object.keys(categories).length == 1) {
            $(`[cat='${Object.keys(categories)[0]}']`).collapse('show');
        }
        */

        if (!exists && value.length == 34 && !value.includes(" ") && addrPattern.test(value)) {
            $('#spinner').show();
            let isValid = await isValidAddr(original);
            if (isValid) {
                $('#spinner').hide();
                vm.$apply(`basic.tempAddr={addr:'${original}',url:'${window.location.pathname + "/search/" + original}'}`);
            } else {
                $('#spinner').hide();
            }
        } else {
            vm.$apply(`basic.tempAddr={addr:'',url:''}`);
        }
    });
});

function submit(type) {
    console.log(type);
    var vm = angular.element($('body')).scope();
    vm.$apply(`main.submit('${type}')`);
}

function resetSideBar() {
    $("#searchBar").val("");
    $("#accordion .addr").toggle(true)
    $("#accordion .category").filter(function () {
        if ($(this).attr('name') != "Home") {
            $('#' + $(this).attr('name')).collapse('hide');
        }

        $(this).toggle(true);
    });
    prevVal = '';
}

function isValidAddr(addr) {
    return new Promise(async resolve => {
        resolve(await $.get("./isValidAddr?addr=" + addr));
    });
}

var dragging = false;

$('#dragbar').mousedown(function (e) {
    e.preventDefault();
    dragging = true;
    var side = $('#sidebar-container');
    $('iframe').css('pointer-events', 'none');
    $(document).mousemove(function (ex) {
        if (ex.pageX + 2 < 425 && ex.pageX + 2 > 50 && dragging) {
            side.width(ex.pageX + 2);
        } else if (ex.pageX + 2 <= 50 && dragging) {
            stopDrag();
            var vm = angular.element($('body')).scope();
            vm.$apply(`basic.toggleSide()`);
        }

        if (side.width() < 85) {
            $(".btn-overlap").hide();
        } else {
            $(".btn-overlap").show();
        }
    });
});

function stopDrag() {
    $('iframe').css('pointer-events', 'auto');
    $(document).unbind('mousemove');
    dragging = false;
}

$(document).mouseup(function (e) {
    if (dragging) {
        stopDrag();
    }
});

$('#accordion').on('hide.bs.collapse', e => {
    var el = $(`[name='${e.target.id}']`).find('i');

    $(el).toggleClass("flip flipped");
});

$('#accordion').on('show.bs.collapse', e => {
    var el = $(`[name='${e.target.id}']`).find('i');
    
    $(el).toggleClass("flipped flip");
});