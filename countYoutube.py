import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from io import BytesIO

# Đọc API Key từ Streamlit secrets
try:
    API_KEY = st.secrets["credentials"]["API_KEY"]
except (KeyError, AttributeError, st.errors.StreamlitSecretNotFoundError) as e:
    st.error(f"Không thể tải API Key từ secrets.toml: {str(e)}")
    API_KEY = None

video_url = "https://www.youtube.com/watch?v=YA74YE1bw1k"  # langson ^_^

if API_KEY:
    st.video(video_url)

    def get_channel_uploads(channel_id):
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.channels().list(part='contentDetails', id=channel_id)
        response = request.execute()
        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return uploads_playlist_id

    def get_videos_from_playlist(playlist_id):
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        videos = []
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                title = item['snippet']['title']
                publish_time = item['snippet']['publishedAt']
                videos.append((video_id, title, publish_time))
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return videos

    def get_video_stats(video_id):
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.videos().list(part='statistics', id=video_id)
        response = request.execute()
        if 'items' in response and len(response['items']) > 0:
            stats = response['items'][0]['statistics']
            return {
                'viewCount': int(stats.get('viewCount', 0)),
                'likeCount': int(stats.get('likeCount', 0)),
            }
        return None

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Video Stats')
        return output.getvalue()

    st.title("YouTube Channel Video Stats")
    st.markdown("**[Lấy ID kênh tại đây](https://seostudio.tools/vi/youtube-channel-id)**")
    channel_id = st.text_input("Nhập ID kênh YouTube:", "UCc_pE2B8AkSK-o1SRMZtL7g")

    if st.button("Lấy Thống Kê Video"):
        if channel_id:
            try:
                uploads_playlist_id = get_channel_uploads(channel_id)
                st.write(f"Playlist ID: {uploads_playlist_id}")  # Debug
                videos = get_videos_from_playlist(uploads_playlist_id)
                st.write(f"Số video tìm thấy: {len(videos)}")  # Debug
                video_stats_list = []
                for video_id, title, publish_time in videos:
                    stats = get_video_stats(video_id)
                    if stats:
                        video_stats_list.append({
                            'Title': title,
                            'Video ID': video_id,
                            'Published At': publish_time,
                            'Views': stats['viewCount'],
                            'Likes': stats['likeCount']
                        })
                if video_stats_list:
                    df = pd.DataFrame(video_stats_list)
                    st.write(f"Số dòng trong bảng: {len(df)}")  # Debug
                    sort_by = st.selectbox("Sắp xếp theo:", ["Lượt xem", "Lượt thích"])
                    if sort_by == "Lượt xem":
                        df = df.sort_values(by='Views', ascending=False)
                    else:
                        df = df.sort_values(by='Likes', ascending=False)
                    df.index = range(1, len(df) + 1)
                    st.dataframe(df[['Title', 'Video ID', 'Published At', 'Views', 'Likes']])
                    st.write("Xem video:")

                    # Nút xuất file Excel
                    excel_data = to_excel(df[['Title', 'Video ID', 'Published At', 'Views', 'Likes']])
                    st.download_button(
                        label="Xuất ra Excel",
                        data=excel_data,
                        file_name=f"youtube_stats_{channel_id}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("Không tìm thấy video nào trong kênh hoặc không có số liệu thống kê.")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {str(e)}")
        else:
            st.warning("Vui lòng nhập ID kênh!")
else:
    st.error("Không thể tải API Key. Ứng dụng sẽ không hoạt động.")