function toggleDrop() {
	let vm = angular.element($('body')).scope();
	vm.$apply('vm.customOff()');
	$('#graphDrop').next().toggle();
}

jQuery('#graphDrop').on('click', toggleDrop);
jQuery('.dropdown-menu').click(function (e) {
	e.stopPropagation();
});

$(document).ready(function () {
	$("#searchBar").on("keyup", function () {
		var value = $(this).val().toLowerCase();
		$("#accordion .list-group-item").filter(function () {
			$(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
		});
	});
});

// Hide submenus
$('#body-row .collapse').collapse('hide');

// Collapse/Expand icon
$('#collapse-icon').addClass('fa-angle-double-left');

// Collapse click
$('[data-toggle=sidebar-colapse]').click(function () {
	SidebarCollapse();
});

function SidebarCollapse() {
	$('.menu-collapsed').toggleClass('d-none');
	$('.sidebar-submenu').toggleClass('d-none');
	$('.submenu-icon').toggleClass('d-none');
	$('#sidebar-container').toggleClass('sidebar-expanded sidebar-collapsed');

	// Treating d-flex/d-none on separators with title
	var SeparatorTitle = $('.sidebar-separator-title');
	if (SeparatorTitle.hasClass('d-flex')) {
		SeparatorTitle.removeClass('d-flex');
	} else {
		SeparatorTitle.addClass('d-flex');
	}

	// Collapse/Expand icon
	$('#collapse-icon').toggleClass('fa-angle-double-left fa-angle-double-right');
}