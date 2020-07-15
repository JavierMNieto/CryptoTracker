main.controller('basicController', ['$scope', '$timeout', basicController]);

main.directive('basicController', function() {
	return {
		controller: 'basicController',
		controllerAs: 'basic'
	}
});

function basicController($scope, $timeout) {
	var basic = this;
	
	basic.toggleBar = true;
	basic.slide 	= false;

	basic.loaded 	= true;
	basic.isCustom 	= false;

	basic.known       = [];
	basic.categories  = [];
	basic.breadcrumbs = [];
	basic.activeCrumb = [];

	

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

	basic.getStyle = function(el, attr) {
		return $(el).css(attr);
	}

	basic.toggleSide = function () {
		var onComplete;
		var width = "0px";

		if (basic.toggleBar) {
			$("#dragcircle i").toggleClass("flipped flip");
			$(".btn-overlap").hide();
			basic.toggleBar = false;
			$("a.drag").addClass("slide-right");
			$("#dragbar").removeClass("resize-cursor");
			
			var startNav = $("#navbar").outerHeight()
			var startFrame = $("#iframe1").height();

			$("#navbar").slideUp({
				progress: function(animation, progress) {
					$("#iframe1").height(startFrame + startNav - $("#navbar").outerHeight());
				}
			});
			
			onComplete = function() {
				if ($("#breadcrumb").hasClass("drag")) {
					$(".arrow-right").addClass("slide-right");
				}
			}
		} else {
			$("#dragcircle i").toggleClass("flip flipped");
			basic.toggleBar = true;
			width = "250px";
			$("#dragbar").addClass("resize-cursor");
			
			var startFrame = $("#iframe1").height();

			$("#navbar").slideDown({
				progress: function(animation, progress) {
					$("#iframe1").height(startFrame - $("#navbar").outerHeight());
				}
			});
			onComplete = function() { 
				$(".btn-overlap").show()
			};
		}
		
		$('#sidebar-container').animate({
			width: width
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

		$(function() {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: "hover"
			});

			$("a.list-group-item").click(function () {
				basic.breadcrumbs = [];
				if ($(".collapse.show").length > 0) {
					var cat = $(`#${$(".collapse.show")[0].id}_heading a`);
					basic.addBreadcrumb({
						link: cat.attr("href"),
						name: cat.text().trim()
					});
				}

				basic.addBreadcrumb({
					link: $(this).attr("href"),
					name: $(this).text().trim()
				});
			});
		});
	}

	function getBreadcrumb(crumb) {
		for (var i = 0; i < basic.breadcrumbs.length; i++) {
			if (basic.breadcrumbs[i].name.toLowerCase().trim() == crumb.name.toLowerCase().trim()) {
				return i;
			}
		}
	
		return -1;
	}

	basic.addBreadcrumb = function (crumb) {
		$('.tooltip').remove();
		var index = getBreadcrumb(crumb);
		
		if (index > -1) {
			basic.breadcrumbs[index] = crumb;
		} else {
			if (basic.breadcrumbs.length > 0 && basic.activeCrumb != basic.breadcrumbs.length - 1) {
				var newCrumbs = [];
				for (var i = 0; i < basic.activeCrumb + 1; i++) {
					newCrumbs.push(basic.breadcrumbs[i]);
				}
				basic.breadcrumbs = newCrumbs;
			}

			basic.breadcrumbs.push(crumb);

			index = basic.breadcrumbs.length - 1;
		}

		basic.activeCrumb = index;

		setTimeout(function() {
			$("#breadcrumb").addClass("slide-right");
			setTimeout(function() {
				if (!$("#dragcircle").hasClass("slide-right") || !$("#dragbar").hasClass("resize-cursor")) {
					$("#breadcrumb").removeClass("slide-right");
				}
			}, 2000);
		}, 250);
	}	

	basic.setTempAddr = function(addr) {
		basic.tempAddr = {
			addr: addr,
			url: window.location.pathname + "/addr/" + addr
		}

		$(function() {
			$("#tempAddr").click(function() {
				basic.addBreadcrumb({
					link: $(this).attr("href"),
					name: $(this).text().trim()
				});
			});
		});
	}

	basic.updateKnown();

	$(function() {
		$("#iframe1").height($("#iframe1").height()-$("#navbar").outerHeight());
	});
}

function receiveMessage(event) {
	if (event.origin == window.location.origin) {
		if (event.data.type == "crumb") {
			let vm = angular.element($('body')).scope();
			vm.$apply(`basic.addBreadcrumb(${JSON.stringify(event.data.crumb)})`);
		}
	}
}

window.addEventListener("message", receiveMessage, false);