main.controller('sessionController', ['$scope', sessionController]);

main.directive('sessionController', function () {
	return {
		controller: 'sessionController',
		controllerAs: 'session'
	}
});

function sessionController($scope) {
	session = this;
	var sessTimeout;

	session.val = '';
	session.valid = false;
	session.reason = 'Must contain 3 or more characters!';

	session.showSession = function (obj) {
		$('a').click(function (event) {
			event.preventDefault();
		});
		$('#overlay').modal('show');
		$(".alert").remove();

		$scope.main.overlay = obj;

		session.val = '';
		session.valid = false;
		session.reason = 'Must contain 3 or more characters!';

		$('[data-toggle="tooltip"]').tooltip({
			trigger: "hover"
		});

		setTimeout(function () {
			$('a').off();
		}, 250);
	}

	session.checkSession = function () {
		$('.tooltip').remove();

		var val = session.val;
		var valid = false;

		if (val.length >= 3 && val.length <= 16 && namePattern.test(val)) {
			valid = null;
			clearTimeout(sessTimeout);

			sessTimeout = setTimeout(async () => {
				$scope.$apply(() => {
					session.valid = null;
				});

				let isValid = await $.get("./isUniqSession?name=" + val);
				session.valid = isValid;
				if (!isValid) {
					session.reason = "A session already exists with this name!";
				}
			}, 500);
		} else if (val.length < 3) {
			session.reason = "Must contain 3 or more characters!";
		} else if (val.length > 16) {
			session.reason = "Must only contain 16 characters or less!";
		} else if (!namePattern.test(val)) {
			session.reason = "Must only contain numbers or letters!";
		}

		if (valid !== null) {
			session.valid = valid;
		}
	}

	session.submit = async function (type) {
		let resp = await $scope.main.submit(type);

		if (type == "addSession" && !resp.toLowerCase().includes("ERROR")) {
			window.location = resp;
		} else if (!resp.toLowerCase().includes("ERROR")) {
			location.reload();
		}
	}

	session.mouseEnter = function(sess) {
		sess = "#" + sess + " .card";
		$(sess + " .card-body").removeClass("overflow");

		height = totalHeight(sess);

		if ($(sess).height() < height) {
			$(sess).animate({
				"max-height": height
			}, 'fast');
		}

	}

	session.mouseExit = function(sess) {
		sess = "#" + sess + " .card";

		$(sess).animate({
			"max-height": "12rem"
		}, 'fast');

		if ($(sess).height() < totalHeight(sess)) {
			$(sess + " .card-body").addClass("overflow");
		}
	}

	
	function totalHeight(sess) {
		return $(sess + " .card-body").outerHeight() + $(sess + " .card-header").outerHeight();
	}

}