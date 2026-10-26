from web.services.cbz_merger import episode_number, sort_episodes

def test_episode_number_supports_chapters():
    assert episode_number("comic-chapter-24.cbz") == 24
    assert episode_number("episode_2.cbz") == 2


