var main = angular
	.module('main', [])
	.controller('mainController', ['$scope', mainController])
	.directive('ngTitle', function($parse) {
		return {
			restrict: "A",
			link: function(scope, element, attr) {
				scope.$watch(attr.ngTitle, function (v) {
					element.tooltip({
						title: v
					})
				});
			}
		};
	});

function mainController($scope) {
	main = this;
	var emailTimeout, userTimeout;

	main.formState   = "";
	main.overlay     = {};
	main.acctInput   = {};
	main.ut = moment().utc().format('HH:mm:ss');
	main.hk = moment().tz('Asia/Hong_Kong').format('HH:mm:ss');

	setInterval(function () {
		$scope.$apply(function () {
			main.ut = moment().utc().format('HH:mm:ss');
			main.hk = moment().tz('Asia/Hong_Kong').format('HH:mm:ss');
		});
	}, 1000);

	main.showAcct    = function (type) {
		$('#overlay').modal('show');
		$(".alert").remove();

		main.overlay = {
			type: type
		};
		
		main.acctInput = {
			user: {
				val: '',
				valid: false,
				reason: 'Must contain 3 or more characters!'
			},
			email: {
				val: '',
				valid: false,
				reason: 'Invalid Email Address!'
			},
			pass: {
				val: '',
				valid: false,
				reason: 'Must contain 5 or more characters!'
			}
		};

		$('[data-toggle="tooltip"]').tooltip({
			trigger: 'hover',
			boundary: "window"
		});
	}

	main.checkUser = function() {
		$('.tooltip').remove();

		var val   = main.acctInput.user.val;
		var valid = false;

		if (val.length >= 3 && val.length <= 16 && namePattern.test(val)) {
			valid = null;
			clearTimeout(userTimeout);

			userTimeout = setTimeout(async () => {
				$scope.$apply(() => {
					main.acctInput.user.valid = null;
				});
				
				let isValid = await $.get("../isUniqUser?username=" + val);
				main.acctInput.user.valid = isValid;
				if (!isValid) {
					main.acctInput.user.reason = "An account already exists with this username!";
				}
			}, 500);
		} else if (val.length < 3) {
			main.acctInput.user.reason = "Must contain 3 or more characters!";
		} else if (val.length > 16) {
			main.acctInput.user.reason = "Must only contain 16 characters or less!";
		} else if (!namePattern.test(val)) {
			main.acctInput.user.reason = "Must only contain numbers or letters!";
		}

		if (valid !== null) {
			main.acctInput.user.valid = valid;
		}
	}

	main.checkEmail = function() {
		$('.tooltip').remove();

		var val   = main.acctInput.email.val;

		if (val.replace(/[^@ || .]/g, "").length == 2) {
			clearTimeout(emailTimeout);

			emailTimeout = setTimeout(async () => {
				$scope.$apply(() => {
					main.acctInput.email.valid = null;
				});
				
				let isValid = await $.get("../isUniqEmail?email=" + val);
				main.acctInput.email.valid = isValid;

				if (!isValid) {
					main.acctInput.email.reason = "An account already exists with this email!";
				}
			}, 500);
		} else {
			main.acctInput.email.reason = "Invalid Email Address!";
			main.acctInput.email.valid  = false;
		}
	}

	main.checkPass = function() {
		$('.tooltip').remove();

		var val   = main.acctInput.pass.val;
		var valid = false;

		if (val.length >= 5 && val.length < 32) {
			valid = true;
		} else if (val.length < 5) {
			main.acctInput.pass.reason = "Must contain 5 or more characters!"
		} else if (val.length < 32) {
			main.acctInput.pass.reason = "Must only contain 32 characters or less!"
		}

		main.acctInput.pass.valid = valid;
	}

	// REVIEW
	main.submit = function(type) {
		return new Promise(async resolve => {
			$(".alert").remove();
			main.formState = "load"; // Change
	
			let resp = await $.ajax({
				url: $(`#${type}`).attr('action'),
				type: 'POST',
				data: $(`#${type}`).serialize()
			});
	
			main.formState = ""; // asdfasdf
	
			console.log(resp);
	
			if (resp.toLowerCase() == "success" && type.includes("sign")) {
				location.reload();
			} else if (resp.toLowerCase() == "error") {
				$("#overlay").prepend('<div class="alert alert-danger alert-dismissible fade show" role="alert"><strong>Error!</strong> You should check in on some of those fields below.<button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button></div>')
			}
			
			resolve(resp);
		});
	}
}