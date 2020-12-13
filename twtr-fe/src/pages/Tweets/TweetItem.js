import React from "react";
import { View, Image, Text, StyleSheet } from "react-native";

const TweetItem = ({ item: tweet }) => {
  return (
    <View style={styles.row}>
      <Image style={styles.rowIcon} source={tweet.pic} />
      <View style={styles.rowData}>
        <Text style={styles.rowDataText}>{`${tweet.date} ${tweet.user} ${tweet.private} ${tweet.aboutme}`}</Text>
        <Text style={styles.rowDataSubText}>{tweet.description}</Text>
      </View>
    </View>
  );
};

//rowIcon: consider adding, to handle BIG images:
//resizeMode: 'contain'
//resizeMode: 'cover'
//resiceMode: 'center'
// https://reactnative.dev/docs/image.html#resizemode
const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    padding: 15,
    marginBottom: 5,
    backgroundColor: "white",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "rgba(0,0,0,0.1)"
  },
  rowIcon: {
    width: 64,
    height: 64,
    marginRight: 20,
    borderRadius: "50%",
    boxShadow: "0 1px 2px 0 rgba(0,0,0,0.1)"
  },
  rowData: {
    flex: 1
  },
  rowDataText: {
    fontSize: 15,
    textTransform: "capitalize",
    color: "#4b4b4b"
  },
  rowDataSubText: {
    fontSize: 13,
    opacity: 0.8,
    color: "#a8a689",
    marginTop: 4
  }
});

export default TweetItem;