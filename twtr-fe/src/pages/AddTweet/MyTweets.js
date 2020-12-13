import React, {useEffect} from 'react'
import MyTweetsContainer from "./MyTweetsContainer";
import AddTweet from "./AddTweet";
import { isAuthorised } from '../../utils/auth'
import {useHistory} from "react-router-dom";

const localStorageAuthKey = 'fwo:auth'
const MyTweets = () => {
    const history = useHistory()
    let user = null
    let isAuth = isAuthorised()
    if (isAuth == false) {
        let _route = '/signin'
        history.push(_route)
    } else {
        const auth = JSON.parse(localStorage.getItem(localStorageAuthKey))
        user = auth.email
    }
    const [tweets, setTweets] = React.useState([]);
    useEffect(() => {
        const fetchData = async () => {
            //zk edited
            const res = await fetch('/api/tweetByUser?user=${user}');
            const { results } = await res.json();
            setTweets([...results]);
        };
        fetchData();
    }, []);

    const handleAddClick = (twitter) => {
        console.log("handleAddClick:  " + twitter.user)
        console.log("tweets length" + tweets.length)
        setTweets([...tweets, twitter]);
    }

    return(
        <div>
            <div>
                <AddTweet handleAddClick={handleAddClick}/>
            </div>
            <div style={{margin:50}}>
                <MyTweetsContainer tweets={tweets}/>
            </div>
        </div>
    )
}
export default MyTweets;

