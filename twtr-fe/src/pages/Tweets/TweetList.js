import React from "react";
import { SwipeableFlatList } from "react-native";
//import {SwipeableFlatList} from 'react-native-swipeable-flat-list';
import TweetItem from "./TweetItem";
import TweetActions from "./TweetActions";

const TweetList = ({ tweets }) => {
  return (
    <SwipeableFlatList
      data={tweets}
      bounceFirstRowOnMount={true}
      maxSwipeDistance={160}
      renderItem={TweetItem}
      renderQuickActions={TweetActions}
    />
  );
};

export default TweetList;
