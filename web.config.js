var path = require('path');

module.exports = {
    mode: "production",
    optimization: {
		minimize: false
	},
    entry: './src/refresh.js',
    output: {
        path: path.join(`${__dirname}/`, 'src'),
        filename: 'bundle.js'
    },
    resolve: {
        modules: [path.resolve(__dirname, '/'), 'node_modules/'],
        descriptionFiles: ['package.json'],
        extensions : ['.js', '.ts', '.json']
    },
    node: {
        fs: 'empty',
        net: 'empty',
        tls: 'empty',
    }
};