import types

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

    def test_from_url(self):
        client = Client.from_url(f'clickhouse://{self.host}', loop=self.loop)

        async def run():
            rv = await client.execute('SELECT 2')
            self.assertEqual(rv, [(2,)])

        self.loop.run_until_complete(run())
        self.loop.run_until_complete(client.disconnect())


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


class IterTestCase(BaseTestCase):
    def test_simple(self):
        async def run():
            result = await self.client.execute_iter(
                'SELECT number FROM system.numbers LIMIT 10'
            )

            self.assertIsInstance(result, types.AsyncGeneratorType)

            self.assertEqual([i async for i in result], list(zip(range(10))))
            self.assertEqual([i async for i in result], [])

        self.loop.run_until_complete(run())

    def test_next(self):
        async def run():
            result = await self.client.execute_iter(
                'SELECT number FROM system.numbers LIMIT 3'
            )

            self.assertIsInstance(result, types.AsyncGeneratorType)

            self.assertEqual(await result.__anext__(), (0, ))
            self.assertEqual(await result.__anext__(), (1, ))
            self.assertEqual(await result.__anext__(), (2, ))

            with self.assertRaises(StopAsyncIteration):
                await result.__anext__()

        self.loop.run_until_complete(run())
