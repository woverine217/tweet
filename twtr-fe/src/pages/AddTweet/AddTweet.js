import React, {useState} from 'react';
import axios from "axios";
import { makeStyles } from '@material-ui/core/styles';
import Input from '@material-ui/core/Input';
import InputLabel from '@material-ui/core/InputLabel';
import InputAdornment from '@material-ui/core/InputAdornment';
import FormControl from '@material-ui/core/FormControl';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import AccountCircle from '@material-ui/icons/AccountCircle';
import Switch from '@material-ui/core/Switch';
import FormControlLabel from '@material-ui/core/FormControlLabel';

const useStyles = makeStyles((theme) => ({
    margin: {
        margin: theme.spacing(15, 20, 2),
    }
}));
const AddTweet = ({ handleAddClick}) => {
    const classes = useStyles();
    const [allValues, setAllValues] = useState({
        user: '',
        pic: '',
        description: '',
        private: false
    });

    const changeHandler = e => {
        setAllValues({...allValues, [e.target.name]: e.target.value})
    }
    const handleChange = (event) => {
        setAllValues({ ...allValues, [event.target.name]: event.target.checked });
    };

    function handleSubmit(event) {
        event.preventDefault()
        //zk edited
        // const ipAdd = window.location.hostname;
        console.log("handleSubmit" + " " + allValues.username)
        handleAddClick(allValues);
        //zk edited
        // axios.post(`http://${ipAdd}:5000/tweet`, {
        axios.post('/api/tweet', {    
            user: allValues.user,
            description: allValues.description,
            private: allValues.private,
            pic: allValues.pic
        });
        console.log(allValues)
    }

    return (
        <div>
            <FormControl className={classes.margin}>
                <InputLabel htmlFor="input-with-icon-adornment">Your Name</InputLabel>
                <Input
                    name="user"
                    onChange={changeHandler}
                    id="input-with-icon-adornment"
                    startAdornment={
                        <InputAdornment position="start">
                            <AccountCircle />
                        </InputAdornment>
                    }
                />
            </FormControl>
            <FormControl className={classes.margin}>
                <InputLabel htmlFor="input-with-icon-adornment">Your Photo</InputLabel>
                <Input
                    name="pic"
                    onChange={changeHandler}
                    id="input-with-icon-adornment"
                    startAdornment={
                        <InputAdornment position="start">
                            <AccountCircle />
                        </InputAdornment>
                    }
                />
            </FormControl>
            <div>
                <TextField
                    name="description"
                    onChange={changeHandler}
                    className={classes.margin}
                    id="input-with-icon-textfield"
                    label="Twitter"
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <AccountCircle />
                            </InputAdornment>
                        ),
                    }}
                />
                <FormControlLabel className={classes.margin}
                    control={<Switch checked={allValues.private} onChange={handleChange} name="private"/>}
                    label="Private"
                />
            </div>
            <Button className={classes.margin} variant="contained" color="secondary" onClick={handleSubmit}>
                POST
            </Button>
        </div>
    );
}
export default AddTweet;
