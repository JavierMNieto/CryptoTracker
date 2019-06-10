(function () {
	'use strict';

	angular
		.module('txs', [])
		.factory('PagerService', PagerService)
		.controller('txsController', ['PagerService', 'filterFilter', '$scope', txs]);

	function txs(PagerService, filter, $scope) {
		var vm = this;
		var order = 'DESC';
		var sort  = 'epoch';

		var edges = []

		vm.txs = [];
		vm.pager = {};
		vm.reverse = false;
		vm.dropText = "Most Recent";
		vm.collapseText = "Show All Transactions"
		vm.isCollapsed = true;
		vm.selection = {
			type: '',
			data: {}
		};

		vm.setPage = function setPage(page) {
			if (vm.pager.totalPages < 1) {
				vm.pager = PagerService.GetPager(totalTxs, page);
			}
			if (page < 1 || page > vm.pager.totalPages) {
				return;
			}

			// get pager object from service
			vm.pager = PagerService.GetPager(totalTxs, page);

			// get current page of items
			var url = `../getTxs?page=${vm.pager.currentPage}&sort=${sort}&order=${order}`;
			if (_name) {
				for (var n = 0; n < _name.length; n++) {
					url += "&name[]=" + _name[n];
				}
			}
			$.get(url, data => {
				$scope.$apply(() => {
					vm.txs = data;
				});
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
			});
		}

		vm.setTxs = function (txs) {
			if (txs == undefined) {
				txs = vm.prevTxs;
			}
			vm.txs = txs;

			//vm.setPage(1);
			vm.selection = {
				type: '',
				data: {}
			};
		}

		vm.collapse = function (isCollapse) {
			if (isCollapse !== undefined) {
				vm.isCollapsed = isCollapse;
			}
			if (vm.isCollapsed) {
				vm.isCollapsed = false;
				vm.collapseText = 'Collapse Transactions';
				$(function () {
					$('input[name="minTime"]').daterangepicker({
						singleDatePicker: true,
						timePicker: true,
						showDropdowns: true,
						minDate: moment.unix($('div[name="dateTimes"]').attr('data-minDate')).format('M/DD/YY hh:mm A'),
						maxDate: moment.unix($('div[name="dateTimes"]').attr('data-maxDate')).format('M/DD/YY hh:mm A'),
						locale: {
							format: 'M/DD/YY hh:mm A'
						}
					});
					$('input[name="maxTime"]').daterangepicker({
						singleDatePicker: true,
						timePicker: true,
						showDropdowns: true,
						minDate: moment.unix($('div[name="dateTimes"]').attr('data-minDate')).format('M/DD/YY hh:mm A'),
						maxDate: moment.unix($('div[name="dateTimes"]').attr('data-maxDate')).format('M/DD/YY hh:mm A'),
						locale: {
							format: 'M/DD/YY hh:mm A'
						}
					});
				});
				var d = new Date();
				d.setDate(d.getDate() - 30);
				vm.graphFilters = {
					node: {
						'balance': {
							min: 0,
							max: vm.maxBal
						}
					},
					edge: {
						'amount': {
							min: 0,
							max: vm.maxTx
						},
						'time': {
							min: moment.unix(d.getTime() / 1000).format('M, DD, YY h:mm:ss A'),
							max: moment.unix(vm.maxTime).format('M, DD, YY h:mm:ss A')
						}
					}
				}
				edges = allEdges.all;
				nodes = allNodes;
			} else if (!vm.isCollapsed) {
				vm.isCollapsed = true;
				vm.collapseText = 'Show All Transactions';
				edges = allEdges.collapsed;
				nodes = allNodes;
				vm.graphFilters = {
					node: {
						'balance': {
							min: 0,
							max: vm.maxBal
						}
					},
					edge: {
						'amount': {
							min: 0,
							max: vm.maxTotalTx
						},
						'avgTx': {
							min: 0,
							max: vm.maxAvgTx
						},
						'txsNum': {
							min: 1,
							max: vm.maxTxsNum
						}
					}
				}
			}
			$(function () {
				$('[data-toggle="tooltip"]').tooltip({
					trigger: 'hover'
				});
			});
			vm.currentId = 0;
			vm.setTxs(allEdges.all);
			vm.prevTxs = vm.txs;
			vm.setFilters();
		}

		vm.setTxs(allEdges);
		$(function () {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: 'hover'
			});
		});
		vm.pager = PagerService.GetPager(totalTxs, 1);
		vm.minTx = minTx;
		vm.lastTx = lastTx;
		/*
		var txInc = orderBy(vm.txs, 'value', false);
		var timeInc = orderBy(vm.txs, 'time', false);

		
		vm.prevTxs = vm.txs;
		
		vm.maxTx = txInc[vm.txs.length - 1].value;
		vm.maxTotalTx = orderBy(allEdges.collapsed, 'value', true)[0].value;
		vm.maxBal = orderBy(allNodes, 'balVal', true)[0].balVal;
		vm.maxAvgTx = orderBy(allEdges.collapsed, 'avgTxVal', true)[0].avgTxVal;
		vm.minTime = timeInc[0].time;
		
		vm.maxTime = moment().unix();
		vm.maxTxsNum = orderBy(allEdges.collapsed, 'txsNum', true)[0].txsNum;
		vm.currentId = 0;
		*/

		vm.sortBy = function (propertyName, reverse) {
			if (propertyName == "time") {
				vm.dropText = "Most Recent";
				sort  = 'epoch';
				order = 'DESC';
			} else if (propertyName == "value" && reverse) {
				vm.dropText = "Transaction Amount ↓";
				sort  = 'amount';
				order = 'DESC';
			} else if (propertyName == "value" && !reverse) {
				vm.dropText = "Transaction Amount ↑";
				sort  = 'amount';
				order = 'ASC';
			}
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
			if (vm.isCollapsed) {
				$('#maxTx').val(vm.maxTotalTx);
			} else {
				$('#maxTx').val(vm.maxTx);
			}
		}

		vm.setMaxBal = function () {
			$('#maxBal').val(vm.maxBal);
		}

		vm.setMaxAvgTx = function () {
			$('#maxAvgTx').val(vm.maxAvgTx);
		}

		vm.setMaxTxsNum = function () {
			$('#maxTxsNum').val(vm.maxTxsNum);
		}

		vm.setFilters = function () {
			let filters = vm.graphFilters;
			let tempNodes;
			let txs = allEdges[(vm.isCollapsed) ? 'collapsed' : 'all'];
			let tempTxs = [];
			for (let nodeFilter in filters.node) {
				tempNodes = filter(allNodes, vm.rangeBy(nodeFilter, filters.node[nodeFilter].min, filters.node[nodeFilter].max))
			}
			let nodeIds = _.map(tempNodes, 'id');
			for (var i = 0; i < txs.length; i++) {
				let isSource = false;
				let isTarget = false;
				for (var n = 0; n < nodeIds.length; n++) {
					if (txs[i].from == nodeIds[n]) {
						isSource = true;
					} else if (txs[i].to == nodeIds[n]) {
						isTarget = true;
					}
					if (isSource && isTarget) {
						tempTxs.push(txs[i]);
						break;
					}
				}
			}
			for (let edgeFilter in filters.edge) {
				if (edgeFilter == 'time') {
					filters.edge[edgeFilter].min = moment(filters.edge[edgeFilter].min, 'M/DD/YY hh:mm A').unix();
					filters.edge[edgeFilter].max = moment(filters.edge[edgeFilter].max, 'M/DD/YY hh:mm A').unix();
				}
				tempTxs = filter(tempTxs, vm.rangeBy(edgeFilter, filters.edge[edgeFilter].min, filters.edge[edgeFilter].max))
				if (edgeFilter == 'time') {
					filters.edge[edgeFilter].min = moment.unix(filters.edge[edgeFilter].min).format('M/DD/YY hh:mm A');
					filters.edge[edgeFilter].max = moment.unix(filters.edge[edgeFilter].max).format('M/DD/YY hh:mm A');
				}
			}
			edges = tempTxs;
			nodes = tempNodes;

			if (vm.isCollapsed) {
				tempTxs = getTxsFromCollapsed(tempTxs);
			}
			vm.setTxs(tempTxs);
			vm.currentId = 0;
			drawGraph(true);
		}

		vm.highlight = function (id, isNode) {
			if (isNode) {
				network.selectNodes([id], false);
				network.focus(id, {
					scale: 1,
					animation: true
				});
				return;
			}
			if (vm.isCollapsed) {
				let source;
				let target;
				for (var i = 0; i < vm.txs.length; i++) {
					if (vm.txs[i].id == id) {
						source = vm.txs[i].source;
						target = vm.txs[i].target;
						break;
					}
				}
				for (var i = 0; i < allEdges.collapsed.length; i++) {
					if (allEdges.collapsed[i].source == source && allEdges.collapsed[i].target == target) {
						id = allEdges.collapsed[i].id
						break;
					}
				}
			}
			network.fit({
				animation: true
			});
			network.selectEdges([id]);
		}

		vm.select = function (properties) {
			vm.prevTxs = vm.txs;
			if (properties.nodes.length > 0) {
				let id = properties.nodes[0];
				let node = data.nodes.get(id);

				if (node.label != "{{search.label}}" && properties.edges.length > 0) {
					let edges = properties.edges;
					let tempEdges = [];
					let txs = allEdges[(vm.isCollapsed) ? 'collapsed' : 'all'];

					for (var i = 0; i < txs.length; i++) {
						for (var e = 0; e < edges.length; e++) {
							if (txs[i].id == edges[e]) {
								tempEdges.push(txs[i]);
								edges.splice(e, 1);
								break;
							}
						}
					}
					if (vm.isCollapsed) {
						tempEdges = getTxsFromCollapsed(tempEdges);
					}
					vm.setTxs(tempEdges);
				} else if (node.label == "{{search.label}}") {
					vm.setTxs();
				}
				vm.selection = {
					type: 'node',
					data: node
				}
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
				return;
			}
			let id = properties.edges[0];
			if (!vm.isCollapsed && id != undefined) {
				let tempEdge = data.edges.get(id);
				vm.selection = {
					type: 'tx',
					data: tempEdge
				}
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
				return;
			}
			for (var i = 0; i < allEdges.collapsed.length; i++) {
				if (allEdges.collapsed[i].id == id) {
					let tempTxs = getTxsFromCollapsed([allEdges.collapsed[i]]);
					vm.setTxs(tempTxs);
					vm.selection = {
						type: 'txTotal',
						data: allEdges.collapsed[i]
					}
					$(function () {
						$('[data-toggle="tooltip"]').tooltip({
							trigger: 'hover'
						});
					});
					return;
				}
			}
		}

		vm.targetBTC = function (txid, from) {
			if (txid == undefined) {
				document.getElementById('graph').style = "cursor: wait";
				network.setOptions({
					"physics": {
						"enabled": true
					}
				});
				txid = vm.selection.data.txid;
				$.get(`https://chain.api.btc.com/v3/tx/${txid}?verbose=3`, response => {
					response = response.data;
					let addr = data.nodes.get(vm.selection.data.to).address
					for (var i = 0; i < response.outputs.length; i++) {
						if (response.outputs[i].addresses[0] == addr) {
							txid = response.outputs[i].spent_by_tx;
							break;
						}
					}
					if (txid == null) {
						setTimeout(function () {
							stopPhysics();
						}, 1000);
						return;
					}
					setTimeout(function () {
						console.log("next tx")
						vm.targetBTC(txid, vm.selection.data.to);
					}, 500)
				});
			} else {
				var date = new Date();
				$.get(`https://chain.api.btc.com/v3/tx/${txid}?verbose=3`, response => {
					response = response.data;
					console.log(response);
					txid = response.outputs[0].spent_by_tx;

					for (var i = 0; i < response.outputs.length; i++) {
						var to = null;
						let tempAllNodes = data.nodes.get();
						for (var j = 0; j < tempAllNodes.length; j++) {
							if (tempAllNodes[j].address == response.outputs[i].addresses[0]) {
								to = tempAllNodes[j].id;
								break;
							}
						}

						if (to === null) {
							vm.currentId++;
							to = vm.currentId;
							data.nodes.add({
								"id": to,
								"label": response.outputs[i].addresses[0],
								"address": response.outputs[i].addresses[0],
								"balance": 0,
								"group": "",
								"lastUpdate": date.getTime() / 1000,
								"url": `https://blockexplorer.com/address/${response.outputs[i].addresses[0]}`,
								"walletName": "none",
								"value": 25.0,
								"img": vm.selection.data.img,
								"title": `Address: ${response.outputs[i].addresses[0]}<br>Balance: ${'None'}<br>Wallet: ${'None'}<br>Last Updated: ${moment().format('YYYY-MM-DD, hh:mm:ss')}`
							});
						}
						vm.currentId++;
						let fromNode = data.nodes.get(from);
						let toNode = data.nodes.get(to);
						data.edges.add({
							"from": from,
							"to": to,
							"id": vm.currentId,
							"value": response.outputs[i].value / satoshi,
							"source": fromNode.label,
							"target": toNode.label,
							"amount": response.outputs[i].value / satoshi,
							"time": response.block_time,
							"txid": response.hash,
							"img": vm.selection.data.img,
							"color": {
								"color": "#F9A540"
							},
							"txidUrl": `https://blockexplorer.com/tx/${response.hash}`,
							"sourceUrl": `https://blockexplorer.com/address/${fromNode.address}`,
							"targetUrl": `https://blockexplorer.com/address/${toNode.address}`,
							"title": `Collapsed: False<br>Txid: ${response.hash}<br>Total: ${response.outputs[i].value/satoshi}<br>Time: ${moment.unix(response.block_time).format('YYYY-MM-DD, hh:mm:ss')}`
						});
						network.focus(to, {
							scale: 0.75,
							locked: true,
							animation: {
								duration: 100
							}
						});
					}
					if (txid == null || response.outputs_count > 1) {
						setTimeout(function () {
							stopPhysics();
						}, 1000);
						return;
					}
					setTimeout(function () {
						console.log("next tx")
						vm.targetBTC(txid, to);
					}, 750);
				});
			}
		}

		vm.sourceBTC = function (txid, to) {
			if (txid == undefined) {
				document.getElementById('graph').style = "cursor: wait";
				network.setOptions({
					"physics": {
						"enabled": true
					}
				});
				txid = vm.selection.data.txid;
				$.get(`https://chain.api.btc.com/v3/tx/${txid}?verbose=3`, response => {
					response = response.data;
					let addr = data.nodes.get(vm.selection.data.from).address
					for (var i = 0; i < response.inputs.length; i++) {
						if (response.inputs[i].prev_addresses[0] == addr) {
							txid = response.outputs[i].spent_by_tx;
							break;
						}
					}
					if (txid == null) {
						setTimeout(function () {
							stopPhysics();
						}, 1000);
						return;
					}
					setTimeout(function () {
						console.log("next tx")
						vm.sourceBTC(txid, vm.selection.data.to);
					}, 500)
				});
			} else {
				var date = new Date();
				$.get(`https://chain.api.btc.com/v3/tx/${txid}?verbose=3`, response => {
					response = response.data;
					console.log(response);
					txid = response.inputs[0].prev_tx_hash;

					for (var i = 0; i < response.inputs.length; i++) {
						var to = null;
						let tempAllNodes = data.nodes.get();
						for (var j = 0; j < tempAllNodes.length; j++) {
							if (tempAllNodes[j].address == response.inputs[i].prev_addresses[0]) {
								to = tempAllNodes[j].id;
								break;
							}
						}

						if (to === null) {
							vm.currentId++;
							to = vm.currentId;
							data.nodes.add({
								"id": to,
								"label": response.inputs[i].prev_addresses[0],
								"address": response.inputs[i].prev_addresses[0],
								"balance": 0,
								"group": "",
								"lastUpdate": date.getTime() / 1000,
								"url": `https://blockexplorer.com/address/${response.inputs[i].prev_addresses[0]}`,
								"walletName": "none",
								"value": 25.0,
								"img": vm.selection.data.img,
								"title": `Address: ${response.inputs[i].prev_addresses[0]}<br>Balance: ${'None'}<br>Wallet: ${'None'}<br>Last Updated: ${moment().format('YYYY-MM-DD, hh:mm:ss')}`
							});
						}
						vm.currentId++;
						let fromNode = data.nodes.get(from);
						let toNode = data.nodes.get(to);
						data.edges.add({
							"from": from,
							"to": to,
							"id": vm.currentId,
							"value": response.inputs[i].prev_value / satoshi,
							"source": fromNode.label,
							"target": toNode.label,
							"amount": response.inputs[i].prev_value / satoshi,
							"time": response.block_time,
							"txid": response.hash,
							"img": vm.selection.data.img,
							"color": {
								"color": "#F9A540"
							},
							"txidUrl": `https://blockexplorer.com/tx/${response.hash}`,
							"sourceUrl": `https://blockexplorer.com/address/${fromNode.address}`,
							"targetUrl": `https://blockexplorer.com/address/${toNode.address}`,
							"title": `Collapsed: False<br>Txid: ${response.hash}<br>Total: ${response.inputs[i].prev_value/satoshi}<br>Time: ${moment.unix(response.block_time).format('YYYY-MM-DD, hh:mm:ss')}`
						});
						network.focus(to, {
							scale: 0.75,
							locked: true,
							animation: {
								duration: 100
							}
						});
					}
					if (txid == null || response.inputs_count > 1) {
						setTimeout(function () {
							stopPhysics();
						}, 1000);
						return;
					}
					setTimeout(function () {
						console.log("next tx")
						vm.sourceBTC(txid, to);
					}, 750);
				});
			}
		}

		function getTxsFromCollapsed(tempTxs) {
			let sources = _.map(tempTxs, 'from');
			let targets = _.map(tempTxs, 'to');
			let temp = [];
			for (var i = 0; i < allEdges.all.length; i++) {
				let isSource = false;
				for (var s = 0; s < sources.length; s++) {
					if (allEdges.all[i].from == sources[s]) {
						isSource = true;
						break;
					}
				}
				if (!isSource) continue;
				let isTarget = false;
				for (var t = 0; t < targets.length; t++) {
					if (allEdges.all[i].to == targets[t]) {
						isTarget = true;
						break;
					}
				}
				if (isSource && isTarget) {
					temp.push(allEdges.all[i]);
				}
			}
			return temp;
		}

		if (edges.length < 50) {
			//vm.collapse(vm.maxTxsNum == 1);
		}
		
		if (vm.maxTxsNum == 1) {
			$('#hide').prop('disabled', true);
			$('#hide').css('background-color', 'grey');
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