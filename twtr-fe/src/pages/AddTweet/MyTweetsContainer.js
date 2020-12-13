import React from "react";
import TweetList from "../Tweets/TweetList";

const MyTweetsContainer = ({ tweets }) => {
    return (
        <TweetList tweets={tweets}/>
    );
}
export default MyTweetsContainer;