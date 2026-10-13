#!/usr/bin/env bash
# Container entrypoint (see compose.yaml).
# The course image's ~/.bashrc sources /tmp/course-active-env.sh in every terminal,
# so pointing it at our env file makes every desktop/shell terminal ROS-ready.
echo "source /project/scripts/project_env.sh" > /tmp/course-active-env.sh
# Close the harmless "can't set wallpaper" popup the desktop shows at startup.
(sleep 10; pkill -x xmessage) >/dev/null 2>&1 &
exec /usr/local/bin/course-desktop
