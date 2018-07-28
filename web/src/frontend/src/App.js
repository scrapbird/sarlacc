import React, { Component } from 'react';
import './App.css';
import ResultTable from './ResultTable';
// import autoBind from 'react-autobind';
import SearchBar from 'material-ui-search-bar'

let lastSearchTerm: String = "";
let lastSearchTime: Date = 0;

function createData(id, subject, from_address, recipients, date_sent, attachments) {
	return { id, subject, from_address, recipients, date_sent, attachments };
}

let data = [
	createData(1, "Test subject", "from@address.com", "<to@example.com, toagain@example.com>", Date("2018/06/05"), "yes"),
	createData(2, "Test subject", "from@address.com", "<to@example.com, toagain@example.com>", Date("2018/06/05"), "yes"),
	createData(3, "Test subject", "from@address.com", "<to@example.com, toagain@example.com>", Date("2018/06/05"), ""),
	createData(4, "Test subject", "from@address.com", "<to@example.com, toagain@example.com>", Date("2018/06/05"), "yes"),
	createData(5, "two subject", "from@address.com", "<to@example.com, toagain@example.com>", Date("2018/06/05"), "yes"),
];

class App extends Component {
	state = { results: [] }
	searchScheduled = false
	scheduledSearch = ""

	constructor(props) {
		super(props)

		this.state.results = data;
		this.runScheduledSearch = this.runScheduledSearch.bind(this)
	}

	search(s) {
		this.setState({
			results: data.filter((i) => i.subject.includes(s)
				|| i.id === s
				|| i.from_address.includes(s)
				|| i.recipients.includes(s)
				|| i.date_sent.includes(s))})
	}

	runScheduledSearch() {
		this.search(this.scheduledSearch)
		this.searchScheduled = false
	}

	scheduleSearch(s) {
		this.scheduledSearch = s
		if (!this.searchScheduled) {
			this.searchScheduled = true
			setTimeout(this.runScheduledSearch, 1000)
		}
	}

	onSearchChange(s) {
		let now = Date.now()

		if (s !== lastSearchTerm) {
			// If the last search was over 1 second ago
			if ((now - lastSearchTime) / 1000 > 1) {
				// Run a search
				lastSearchTime = now
				lastSearchTerm = s
				this.search(s)
			} else {
				// Schedule another search
				this.scheduleSearch(s)
			}
		}

	}

	onRequestSearch(s) {
		this.search(s)
	}

	render() {
		return (
			<div className="App">

			<SearchBar
			autoFocus
			onChange={(s) => this.onSearchChange(s)}
			onRequestSearch={(s) => this.onRequestSearch(s)}
			/>

			<div style={{padding: 0, margin: 0, marginTop: 1 }}/>

			<ResultTable results={this.state.results}/>

			</div>
		);
	}
}

export default App;
