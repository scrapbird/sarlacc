import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

const styles = theme => ({
	root: {
		width: '100%',
		overflowX: 'auto',
	},
	table: {
		minWidth: 700,
	},
});

class ResultTable extends Component {
	render() {
		return (
			<Paper className={this.root}>
			<Table className={this.table}>
			<TableHead>
			<TableRow>
			<TableCell numeric>ID</TableCell>
			<TableCell>Subject</TableCell>
			<TableCell>From Address</TableCell>
			<TableCell>Recipients</TableCell>
			<TableCell>Date Sent</TableCell>
			<TableCell numeric>Attachment Count</TableCell>
			</TableRow>
			</TableHead>
			<TableBody>
			{this.props.results.map(n => {
				return (
					<TableRow key={n.id}>
					<TableCell numeric component="th" scope="row">
					{n.id}
					</TableCell>
					<TableCell>{n.subject}</TableCell>
					<TableCell>{n.from_address}</TableCell>
					<TableCell>{n.recipients}</TableCell>
					<TableCell>{n.date_sent}</TableCell>
					<TableCell>{n.attachments.length === 0 ? "" : n.attachments.length}</TableCell>
					</TableRow>
				);
			})}
			</TableBody>
			</Table>
			</Paper>
		);
	}
}

ResultTable.propTypes = {
	classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(ResultTable);

