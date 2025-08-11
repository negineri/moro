"""ListRecordingsUseCase のテスト

TDD Red Phase: ユースケーステスト作成
"""

from unittest.mock import Mock

from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType
from moro.modules.epgstation.usecases import ListRecordingsUseCase


class TestListRecordingsUseCase:
    """録画一覧取得ユースケースのテスト"""

    def test_should_return_formatted_table_when_recordings_exist(self) -> None:
        """正常系：録画データのテーブル表示テスト"""
        # テストデータの準備
        video_file1 = VideoFile(
            id=1,
            name="テスト番組.ts",
            filename="test_program.ts",
            type=VideoFileType.TS,
            size=1073741824,  # 1GB
        )
        video_file2 = VideoFile(
            id=2,
            name="テスト番組.mp4",
            filename="test_program.mp4",
            type=VideoFileType.ENCODED,
            size=536870912,  # 512MB
        )

        recording = RecordingData(
            id=123,
            name="テスト番組タイトル",
            start_at=1640995200000,  # 2022-01-01 00:00:00 JST
            end_at=1640998800000,  # 2022-01-01 01:00:00 JST
            video_files=[video_file1, video_file2],
            is_recording=False,
            is_protected=True,
        )

        # モックリポジトリの設定
        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)

        # テスト実行
        result = usecase.execute(limit=100)

        # アサーション
        assert isinstance(result, str)
        assert "テスト番組タイトル" in result
        assert "test_program.ts" in result
        assert "test_program.mp4" in result
        assert "TS" in result
        assert "ENCODED" in result
        assert "1.00GB" in result
        assert "512.0MB" in result

        # リポジトリが正しく呼ばれたことを確認
        mock_repository.get_all.assert_called_once_with(limit=100)

    def test_should_return_empty_message_when_no_recordings_found(self) -> None:
        """録画データが0件の場合のメッセージテスト"""
        # モックリポジトリ（空の結果）
        mock_repository = Mock()
        mock_repository.get_all.return_value = []

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)

        # テスト実行
        result = usecase.execute()

        # アサーション
        assert result == "録画データが見つかりませんでした。"

    def test_should_display_all_video_files_when_multiple_files_exist(self) -> None:
        """複数ビデオファイルの表示確認テスト"""
        # 3つのビデオファイルを持つ録画データ
        video_files = [
            VideoFile(id=1, name="file1.ts", filename="file1.ts", type=VideoFileType.TS, size=1024),
            VideoFile(
                id=2, name="file2.mp4", filename="file2.mp4", type=VideoFileType.ENCODED, size=2048
            ),
            VideoFile(id=3, name="file3.ts", filename="file3.ts", type=VideoFileType.TS, size=4096),
        ]

        recording = RecordingData(
            id=456,
            name="複数ファイル番組",
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=video_files,
            is_recording=False,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # 各ビデオファイルが個別行として表示されることを確認
        lines = result.split("\n")
        data_lines = [line for line in lines if "456" in line]  # 録画IDを含む行

        assert len(data_lines) == 3  # 3つのビデオファイル = 3行
        assert "file1.ts" in result
        assert "file2.mp4" in result
        assert "file3.ts" in result

    def test_should_handle_recording_without_video_files(self) -> None:
        """ビデオファイルがない録画データの表示テスト"""
        recording = RecordingData(
            id=789,
            name="ファイルなし番組",
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=[],  # 空のリスト
            is_recording=True,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # ビデオファイルがない場合はN/Aが表示されることを確認
        assert "ファイルなし番組" in result
        assert "N/A" in result
        lines = result.split("\n")
        data_lines = [line for line in lines if "789" in line]
        assert len(data_lines) == 1  # 1行のみ表示

    def test_should_truncate_long_titles_when_title_exceeds_limit(self) -> None:
        """長いタイトルの切り詰め処理テスト"""
        long_title = "あ" * 50  # 50文字の長いタイトル

        video_file = VideoFile(
            id=1, name="test.ts", filename="test.ts", type=VideoFileType.TS, size=1024
        )

        recording = RecordingData(
            id=999,
            name=long_title,
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=[video_file],
            is_recording=False,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # タイトルが40文字+...で切り詰められることを確認
        truncated_title = "あ" * 40 + "..."
        assert truncated_title in result
        assert long_title not in result  # 元の長いタイトルは含まれない

    def test_should_handle_repository_exception_gracefully(self) -> None:
        """リポジトリ例外の適切な処理テスト"""
        mock_repository = Mock()
        mock_repository.get_all.side_effect = RuntimeError("API接続エラー")

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # エラーメッセージが返されることを確認
        assert "エラー: 録画一覧の取得に失敗しました" in result
        assert "API接続エラー" in result

    def test_should_format_start_time_correctly(self) -> None:
        """開始時刻の表示フォーマットテスト"""
        video_file = VideoFile(
            id=1, name="test.ts", filename="test.ts", type=VideoFileType.TS, size=1024
        )

        recording = RecordingData(
            id=100,
            name="時刻テスト番組",
            start_at=1672531200000,  # 2023-01-01 00:00:00 UTC
            end_at=1672534800000,  # 2023-01-01 01:00:00 UTC
            video_files=[video_file],
            is_recording=False,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # 日時フォーマットが正しく表示されることを確認（UTCでの時刻）
        # recording.formatted_start_time プロパティを直接テスト
        assert recording.formatted_start_time in result

    def test_should_handle_mixed_recording_scenarios(self) -> None:
        """複合シナリオ（ファイルありなし混在）のテスト"""
        # ファイルありの録画
        recording_with_files = RecordingData(
            id=1,
            name="ファイルあり",
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=[
                VideoFile(
                    id=1, name="file.ts", filename="file.ts", type=VideoFileType.TS, size=1024
                )
            ],
            is_recording=False,
            is_protected=True,
        )

        # ファイルなしの録画
        recording_without_files = RecordingData(
            id=2,
            name="ファイルなし",
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=[],
            is_recording=True,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording_with_files, recording_without_files]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # 両方の録画が適切に表示されることを確認
        assert "ファイルあり" in result
        assert "ファイルなし" in result
        assert "file.ts" in result
        assert "N/A" in result

    def test_should_use_filename_or_name_for_display(self) -> None:
        """ファイル名の表示優先度テスト"""
        # filename がある場合
        video_file_with_filename = VideoFile(
            id=1, name="表示名.ts", filename="actual_filename.ts", type=VideoFileType.TS, size=1024
        )

        # filename が空の場合
        video_file_without_filename = VideoFile(
            id=2, name="表示名のみ.ts", filename="", type=VideoFileType.TS, size=2048
        )

        recording = RecordingData(
            id=888,
            name="ファイル名テスト",
            start_at=1640995200000,
            end_at=1640998800000,
            video_files=[video_file_with_filename, video_file_without_filename],
            is_recording=False,
            is_protected=False,
        )

        mock_repository = Mock()
        mock_repository.get_all.return_value = [recording]

        usecase = ListRecordingsUseCase(recording_repository=mock_repository)
        result = usecase.execute()

        # filename がある場合は filename が優先され、ない場合は name が使用される
        assert "actual_filename.ts" in result
        assert "表示名のみ.ts" in result
