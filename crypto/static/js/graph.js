function fullGraph() {
	document.getElementById('graph').requestFullscreen();
}

function toggleDarkMode() {
	if ($('#graph').css('background-color') == "rgb(0, 0, 0)") {
		$('#graph').css('background-color', 'white');
		network.setOptions({
			"nodes": {
				"font": {
					"color": "#000000"
				}
			}
		});
	} else {
		$('#graph').css('background-color', 'black');
		network.setOptions({
			"nodes": {
				"font": {
					"color": "#ffffff"
				}
			}
		});
	}
}

// This method is responsible for drawing the graph, returns the drawn network
function drawGraph(stop, graph) {
	//return new Promise(resolve => {
		var container = document.getElementById('graph');
		//container.style = "cursor: wait";

		// adding nodes and edges to the graph
		data = {
			nodes: new vis.DataSet(graph.nodes),
			edges: new vis.DataSet(graph.edges)
		};

		let vm = angular.element($('body')).scope();

		var solver = "forceAtlas2Based";

		if (totalTxs < 2000) {
			solver = "repulsion";
		}

		var options = {
			"nodes": {
				"scaling": {
					"min": 25,
					"max": 200
				},
				"shape": "dot",
				"borderWidthSelected": 1,
				"font": {
					"color": "#ffffff"
				},
				"color": {
					"highlight": {
						"border": "#1f8766",
						"background": "#e5ff00"
					}
				}
			},
			"edges": {
				"arrows": {
					"to": {
						"enabled": true
					}
				},
				"scaling": {
					"min": 1,
					"max": 25
				},
				"arrowStrikethrough": false,
				"color": {
					"highlight": "#e5ff00",
					"hover": "#0062ff"
				},
				"smooth": {
					"type": "dynamic",
					"forceDirection": "none"
				},
				"font": {
					"color": "#000000"
				}
			},
			"groups": {
				"useDefaultGroups": true,
				"usdt": {
					"color": {
						"background": "#26A17B",
						"border": "#1f8766",
					}
				}
			},
			"interaction": {
				"dragNodes": true,
				"hideEdgesOnDrag": false,
				"hideNodesOnDrag": false,
				"hover": true,
				"tooltipDelay": 100,
				"hoverConnectedEdges": true
			},
			"layout": {
				"improvedLayout": false
			},
			"physics": {
				'stabilization': {
					'enabled': true,
					'iterations': 2000,
					'updateInterval': 25
				},
				"repulsion": {
					"nodeDistance": 400,
					"springLength": 300
				},
				"forceAtlas2Based": {
					"avoidOverlap": 0.85
				},
				"enabled": true,
				"solver": solver
			}
		};
		network = new vis.Network(container, data, options);

		network.on("stabilizationProgress", function (params) {
			var maxWidth = 496;
			var minWidth = 20;
			var widthFactor = params.iterations / params.total;
			var width = Math.max(minWidth, maxWidth * widthFactor);

			document.getElementById('bar').style.width = width + 'px';
			document.getElementById('text').innerHTML = Math.round(widthFactor * 100) + '%';
		});
		
		network.once("stabilizationIterationsDone", function () {
			$('#text').text('100%');
			$('#bar').css('width', '496px');
			$('loadingBar').css('opacity', 0);
			vm.$apply(`vm.loadedGraph()`);
			setTimeout(function () {
				$('#loadingBar').hide();
				if (stop) {
					stopPhysics(graph);
				}

			}, 500);
		});

		network.on('click', properties => {
			vm.$apply(`vm.select(${JSON.stringify(properties)})`);
		});

		network.on('deselectEdge', () => {
			var tempNum = 0;
			data.edges.forEach(edge => {
				tempNum += edge.txsNum;
			});
			totalTxs = tempNum;
			vm.$apply('vm.selCollapsed = [];vm.setPage(1);');
			clicked  = false;
		});

		network.on('deselectNode', () => {
			var tempNum = 0;
			data.edges.forEach(edge => {
				tempNum += edge.txsNum;
			});
			totalTxs = tempNum;
			vm.$apply('vm.selection = undefined;');
			clicked  = false;
		});

		//return resolve(network);
	//});
}

////////////////////
//drawGraph();

function stopPhysics(graph) {
	setTimeout(function () {
		network.setOptions({
			"physics": {
				"enabled": false
			}
		});
		network.fit({
			animation: true
		});
		document.getElementById('graphContainer').style = "cursor: auto";
		$('#filterBtn').prop('disabled', false);
	}, graph.edges.length * 5);
}