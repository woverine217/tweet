import React, { useEffect } from 'react';
import TweetList from "./TweetList";
import {makeStyles} from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
    margin: {
        margin: theme.spacing(20),
    }
}));

const THome = () => {
    const classes = useStyles();
  const [tweets, setTweets] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    const fetchData = async () => {
    //zk edited
	  const res = await fetch('/api/tweets-week-results');
      const { results } = await res.json();
      console.log(results);
      setTweets([...results]);
	  setLoading(false);
    };
    fetchData();
  }, []);

  return (
      <div style={{margin:80}}>
	    <TweetList tweets={tweets} />
      </div>
  );
}

export default THome;
