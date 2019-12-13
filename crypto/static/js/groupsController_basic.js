main.controller('basicController', ['$scope', basicController]);

main.directive('basicController', function() {
	return {
		controller: 'basicController',
		controllerAs: 'basic'
	}
});

function basicController($scope) {
	var basic = this;
	
	basic.toggleBar = true;
	basic.loaded 	 = true;
	basic.isCustom = false;

	basic.known = [];
	basic.categories = [];

	basic.tempAddr = {
		addr: '',
		url: ''
	};

	basic.sortGroups = function(group) {
		if (basic.name == "Home") {
			return -1;
		}
		return basic.name;
	}

	basic.startLoader = function () {
		basic.loaded = false;
		$('iframe').contents().find('body').html("");
	}

	$('iframe').on('load', function () {
		$scope.$apply(function () {
			basic.loaded = true;
		});
	});

	basic.toggleSide = function () {
		var onComplete;
		if (basic.toggleBar) {
			var sWidth = $('#sidebar-container').width();
			$('#sidebar-container').width(sWidth);
			$('#sidebar-container').removeClass('col-2');
			onComplete = () => {
				basic.toggleBar = false;
				$('#collapseBtn').removeClass('dropleft').addClass('dropright');
				$('#frame').removeClass('col');
				$('#iframe1').addClass('fixFrame');
			}
		} else {
			$('#frame').addClass('col');
			$('#iframe1').removeClass('fixFrame');
			onComplete = () => {
				basic.toggleBar = true;
				$('#collapseBtn').removeClass('dropright').addClass('dropleft');
				$('#sidebar-container').addClass('col-2');
			}
		}
		$('#sidebar-container').animate({
			width: 'toggle'
		}, 'slow', onComplete);
	}

	function getCollapsed() {
		var cats = $("#accordion .category").toArray();

		for (let i = 0; i < cats.length; i++) {
			var el = $(`#${$(cats[i]).attr("name")}`);
			if ($(el).hasClass("show")) {
				return el.attr("id");
			}
		}

		return null;
	}

	basic.updateKnown = async function() {
		var collapsed = getCollapsed();
		basic.known = await $.get(window.location.pathname + "/getKnown" + window.location.search);
		categories = [];
		for (var i = 0; i < basic.known.length; i++) {
			categories.push(basic.known[i].name);
		}
		$scope.$apply(() => {
			basic.categories = categories;
		});

		if ($(`#${collapsed}`)) {
			setTimeout(function() {
				$(`#${collapsed}`).collapse('show');
			}, 500);
		}

		$(function () {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: "hover"
			});
		});
	}

	basic.updateKnown();
}