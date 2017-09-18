from clickhouse_driver import errors

from aioch import Client
from tests.testcase import BaseTestCase


class PacketsTestCase(BaseTestCase):
    def create_client(self):
        return Client(
            self.host, self.port, self.database, 'wrong_user', loop=self.loop
        )

    def test_exception_on_hello_packet(self):
        async def run():
            with self.assertRaises(errors.ServerException) as e:
                await self.client.execute('SHOW TABLES')

            # Simple exception formatting checks
            exc = e.exception
            self.assertIn('Code:', str(exc))
            self.assertIn('Stack trace:', str(exc))

        self.loop.run_until_complete(run())


class SelectTestCase(BaseTestCase):
    def test_simple_select(self):
        async def run():
            rv = await self.client.execute('SELECT 2')
            self.assertEqual(rv, [(2,)])

        self.loop.run_until_complete(run())


class ProgressTestCase(BaseTestCase):
    def test_select_with_progress(self):
        async def run():
            progress = await self.client.execute_with_progress('SELECT 2')

            progress_rv = []
            async for x in progress:
                progress_rv.append(x)

            self.assertEqual(progress_rv, [(1, 0)])
            rv = await progress.get_result()
            self.assertEqual(rv, [(2,)])

        self.loop.run_until_complete(run())

    def test_select_with_progress_error(self):
        async def run():
            with self.assertRaises(errors.ServerException):
                progress = await self.client.execute_with_progress(
                    'SELECT error'
                )
                await progress.get_result()

        self.loop.run_until_complete(run())

    def test_select_with_progress_no_progress_unwind(self):
        async def run():
            progress = await self.client.execute_with_progress('SELECT 2')
            self.assertEqual(await progress.get_result(), [(2,)])

        self.loop.run_until_complete(run())

    def test_select_with_progress_cancel(self):
        async def run():
            await self.client.execute_with_progress('SELECT 2')
            rv = await self.client.cancel()
            self.assertEqual(rv, [(2,)])

        self.loop.run_until_complete(run())
