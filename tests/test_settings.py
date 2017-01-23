import redis_helper as rh


class TestEnv:
    def test_app_env_is_test(self):
        assert rh.APP_ENV == 'test'

    def test_redis_url_ends_with_9(self):
        redis_url = rh.get_setting('redis_url')
        assert redis_url is not '' and redis_url.endswith('9')
