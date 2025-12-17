#!/bin/sh

URL="localhost:8193"
if [ "$1" != "" ]
  then
    URL="$1"
fi

TOKEN=`curl -s -X POST -H "Content-Type: application/json" --data @user.json http://$URL/api/token | jq -r ".access_token"`

RES=`curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @athlete_req1.json http://$URL/api/athlete | jq -r ".athlete_key"`

if [ "$RES" == "" ]
  then
    echo "FAIL"
    exit 1
fi

# curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @workout.json http://$URL/api/workout

curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @workout.json http://$URL/api/workout_search


# curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @blank.json http://$URL/api/workout_autotrain

# curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @blank.json http://$URL/api/summary_load

exit 0

#curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @activity_req1.json http://$URL/api/activity

#curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @activity_req1.json http://$URL/api/summary_pmc

curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @activity_req1.json http://$URL/api/summary_heart_rate_zone

echo ""

curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @activity_req1.json http://$URL/api/summary_power_zone

# RES=`curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" --data @activity_req1.json http://$URL/api/activity | jq -r ".username"`

# if [ "$RES" != "balderson" ]
#   then
#     echo "FAIL"
#     exit 1
# fi


echo "SUCCESS"

