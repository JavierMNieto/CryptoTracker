var iFrameLoad = true;

function toggleIFrame() {
	if (iFrameLoad) {
		$('#body').show();
		$('#iframe').hide();
		iFrameLoad = false;
	} else {
		$('#body').hide();
		$('#iframe').show();
		iFrameLoad = true;
	}
}

(function () {
	'use strict';

	angular
		.module('txs', [])
		.factory('PagerService', PagerService)
		.controller('txsController', ['PagerService', 'filterFilter', '$scope', txs]);

	function txs(PagerService, filter, $scope) {
		var vm = this;
		var order = 'DESC';
		var sort = 'epoch';
		var graph = {
			nodes: [],
			edges: []
		};
		$('#loadingBar').hide();
		$('#iframe').hide();
		$('#body').show();

		vm.selCollapsed = [];

		vm.txs = [];
		vm.pager = {};
		vm.dropText = "Most Recent";
		vm.collapseText = "Show All Transactions";
		vm.selection;

		vm.pager = PagerService.GetPager(totalTxs, 1);
		vm.minTx = minTx;
		vm.lastTx = lastTx;

		vm.currentId = 0;

		vm.savedPages = {};

		vm.graphFilters = {
			minBal: -1,
			maxBal: 1e99,
			minTx: minTx,
			maxTx: 1e99,
			minTime: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
			maxTime: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
			minTotal: -1,
			maxTotal: 1e99,
			minTxsNum: -1,
			maxTxsNum: 1e99,
			minAvg: -1,
			maxAvg: 1e99
		}
		
		$(function () {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: 'hover'
			});
		});
		$(function () {
			$('input[name="minTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				minDate: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
				maxDate: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
				locale: {
					format: 'M/DD/YY hh:mm A'
				}
			});
			$('input[name="maxTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				minDate: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
				maxDate: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
				locale: {
					format: 'M/DD/YY hh:mm A'
				}
			});
		});

		vm.setPage = function setPage(page) {
			if (vm.pager.totalPages < 1) {
				vm.pager = PagerService.GetPager(totalTxs, page);
			}
			if (page < 1 || page > vm.pager.totalPages) {
				return;
			}

			// get pager object from service
			vm.pager = PagerService.GetPager(totalTxs, page);
			$('[data-toggle="tooltip"]').tooltip('hide');

			if (vm.savedPages["" + page]) {
				vm.txs = vm.savedPages["" + page];
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
				return;
			}

			$('#txList').fadeTo(Math.max(totalTxs/50, 100), 0, () => {
				// get current page of items
				var url = `../getTxs?page=${vm.pager.currentPage - 1}&sort=${sort}&order=${order}`;

				if (_addr == null && vm.selection !== undefined && vm.selection.title.includes('Name:')) {
					url += `&addr[]=${vm.selection.addr}`;
				} else if (vm.selCollapsed.length > 0) {
					for (var i = 0; i < vm.selCollapsed.length; i++) {
						url += `&sender[]=${vm.selCollapsed[i].sender}&receiver[]=${vm.selCollapsed[i].receiver}`;
					}
				} else if (_addr) {
					for (var n = 0; n < _addr.length; n++) {
						url += "&addr[]=" + _addr[n];
					}
				}

				for (let filter in vm.graphFilters) {
					var val = vm.graphFilters[filter];
					if (filter.toLowerCase().includes('time')) {
						val = moment(val, 'M/DD/YY hh:mm A').valueOf()/1000;
					}
					url += `&${filter}=${val}`;
				}

				$.get(url, data => {
					$scope.$apply(() => {
						vm.txs = data;
					});
					vm.savedPages["" + page] = data;
					
					$('#txList').fadeTo("fast", 1);
					$(function () {
						$('[data-toggle="tooltip"]').tooltip({
							trigger: 'hover'
						});
					});
				});
			});
		}

		vm.sortBy = function (propertyName, reverse) {
			if (propertyName == "time") {
				vm.dropText = "Most Recent";
				sort = 'epoch';
				order = 'DESC';
			} else if (propertyName == "value" && reverse) {
				vm.dropText = "Transaction Amount ↓";
				sort = 'amount';
				order = 'DESC';
			} else if (propertyName == "value" && !reverse) {
				vm.dropText = "Transaction Amount ↑";
				sort = 'amount';
				order = 'ASC';
			}
			vm.savedPages = {};
			vm.setPage(vm.pager.currentPage);
			//vm.txs = $.get(`../getTxs?page=${vm.pager.currentPage}&sort=${sort}&order=${order}`);
		}

		vm.rangeBy = function (fieldName, minValue, maxValue) {
			if (minValue === undefined) minValue = 0;
			if (maxValue === undefined) maxValue = Number.MAX_VALUE;

			return function predicateFunc(item) {
				return minValue <= item[fieldName] && item[fieldName] <= maxValue;
			};
		}

		vm.setMaxTx = function () {
			$('#maxTx').val(1e99);
		}

		vm.setMaxBal = function () {
			$('#maxBal').val(1e99);
		}

		vm.setMaxAvgTx = function () {
			$('#maxAvgTx').val(1e99);
		}

		vm.setMaxTxsNum = function () {
			$('#maxTxsNum').val(1e99);
		}

		vm.setFilters = function (isReset) {
			document.getElementById('graphContainer').style = "cursor: wait";
			$('#text').text('0%')
			$('#bar').css('width', '20px');
			$('loadingBar').css('opacity', 1);
			$('#loadingBar').show();
			$('#resetBtn').prop('disabled', true);
			$('#filterBtn').prop('disabled', true);
			var url = `../getGraph?`;
			$('[data-toggle="tooltip"]').tooltip('hide');
			if (_addr) {
				for (var n = 0; n < _addr.length; n++) {
					url += "&addr[]=" + _addr[n];
				}
			}
			if (!isReset) {
				for (let filter in vm.graphFilters) {
					var val = vm.graphFilters[filter]
					if (filter.toLowerCase().includes('time')) {
						val = moment(val, 'M/DD/YY hh:mm A').valueOf()/1000;
					}
					url += `&${filter}=${val}`;
				}
			} else {
				vm.graphFilters = {
					minBal: -1,
					maxBal: 1e99,
					minTx: minTx,
					maxTx: 1e99,
					minTime: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
					maxTime: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
					minTotal: -1,
					maxTotal: 1e99,
					minTxsNum: -1,
					maxTxsNum: 1e99,
					minAvg: -1,
					maxAvg: 1e99
				}
			}
			url = url.replace('?&', '?');
			$.get(url, resp => {
				if (resp.nodes.length == 0 && resp.edges.length == 0) {
					$('#loadingBar').hide();
					$('#graph').html('<div style="margin-top: 20%">Nothing Found.</div>');
					document.getElementById('graphContainer').style = "cursor: auto";
					$('#resetBtn').prop('disabled', false);
					$('#filterBtn').prop('disabled', false);
				} else {
					graph = {
						nodes: resp.nodes,
						edges: resp.edges
					}
					totalTxs = resp.totalTxs;
					drawGraph(true, graph);
					vm.savedPages = {};
					vm.setPage(1);
					$("#resetBtn").attr('data-original-title', 'Reset Graph');
				}
			});
			
		}

		vm.highlight = function (id, isNode) {
			if (!graph) return;

			if (isNode) {
				network.selectNodes([id], false);
				network.focus(id, {
					scale: 1,
					animation: true
				});
				return;
			}
			let source = id.source;
			let target = id.target;
			var edgeId;

			for (var i = 0; i < graph.edges.length; i++) {
				if (graph.edges[i].source == source && graph.edges[i].target == target) {
					edgeId = graph.edges[i].id
					break;
				}
			}

			console.log(edgeId);

			if (edgeId) {
				network.fit({
					animation: true
				});
				network.selectEdges([edgeId]);
			}
		}

		vm.select = function (properties) {
			if (properties.nodes.length > 0) {
				let id = properties.nodes[0];
				let node = data.nodes.get(id);
				if (node.label.toLowerCase() === $('#name').text().toLowerCase()) {
					return;
				}
				vm.selection = node;
			}
			if (properties.edges.length > 0) {
				var tempTxs = properties.edges
				var tempNum = 0;
				for (var i = 0; i < tempTxs.length; i++) {
					let tx = data.edges.get(tempTxs[i]);
					vm.selCollapsed.push({
						sender: tx.sourceAddr,
						receiver: tx.targetAddr
					});
					tempNum += tx.txsNum;
				}
				totalTxs = tempNum;
			}
			if (properties.edges.length > 0 || properties.nodes.length > 0) {
				vm.savedPages = {};
				vm.setPage(1);
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
			}
		}

		if (totalTxs < 2000) {
			vm.setFilters(false);
		} else {
			vm.setPage(1);
		}
	}

	function PagerService() {
		// service definition
		var service = {};

		service.GetPager = GetPager;

		return service;

		// service implementation
		function GetPager(totalItems, currentPage, pageSize) {
			// default to first page
			currentPage = currentPage || 1;

			// default page size is 10
			pageSize = pageSize || 10;

			// calculate total pages
			var totalPages = Math.ceil(totalItems / pageSize);

			var startPage, endPage;
			if (totalPages <= 10) {
				// less than 10 total pages so show all
				startPage = 1;
				endPage = totalPages;
			} else {
				// more than 10 total pages so calculate start and end pages
				if (currentPage <= 6) {
					startPage = 1;
					endPage = 10;
				} else if (currentPage + 4 >= totalPages) {
					startPage = totalPages - 9;
					endPage = totalPages;
				} else {
					startPage = currentPage - 5;
					endPage = currentPage + 4;
				}
			}

			// calculate start and end item indexes
			var startIndex = (currentPage - 1) * pageSize;
			var endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);

			// create an array of pages to ng-repeat in the pager control
			var pages = _.range(startPage, endPage + 1);

			// return object with all pager properties required by the view
			return {
				totalItems: totalItems,
				currentPage: currentPage,
				pageSize: pageSize,
				totalPages: totalPages,
				startPage: startPage,
				endPage: endPage,
				startIndex: startIndex,
				endIndex: endIndex,
				pages: pages
			};
		}
	}
})();