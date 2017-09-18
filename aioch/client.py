import asyncio

from clickhouse_driver.client import Client as BlockingClient, QueryResult

from .utils import run_in_executor


class Progress(object):
    def __init__(self, result, async_client):
        self.async_client = async_client
        self._client = async_client._client
        self.result = result
        self.rows_read, self.approx_rows_to_read = 0, 0

        # We shouldn't read more packets, if already got StopAsyncIteration.
        # Mark query as completed if all packets are read.
        self.done = False

        super(Progress, self).__init__()

    def __aiter__(self):
        return self

    async def __anext__(self):
        # There is not async generators till Python 3.6.
        # That's why some code from client moved here.
        try:
            read_more = True
            while read_more is True:
                read_more = await self.read_packet()

            if read_more is None:
                self.done = True
                raise StopAsyncIteration

            return read_more

        except StopAsyncIteration:
            raise

        except (Exception, KeyboardInterrupt):
            await self.async_client.disconnect()
            raise

    async def read_packet(self):
        packet = await self.async_client.run_in_executor(
            self._client.receive_packet
        )
        if not packet:
            return

        if packet is True:
            return True

        progress = getattr(packet, 'progress', None)
        if progress:
            if progress.new_total_rows:
                self.approx_rows_to_read = progress.new_total_rows

            self.rows_read += progress.new_rows

            return self.rows_read, self.approx_rows_to_read
        else:
            self._client.store_query_result(packet, self.result)

        return True

    async def get_result(self):
        if not self.done:
            async for _ in self:  # noqa: ignore=F4841
                pass

        return self.result.get_result()


class Client(object):
    def __init__(self, *args, **kwargs):
        self._loop = kwargs.pop('loop', None) or asyncio.get_event_loop()
        self._executor = kwargs.pop('executor', None)
        self._client = BlockingClient(*args, **kwargs)

        super(Client, self).__init__()

    def run_in_executor(self, *args, **kwargs):
        return run_in_executor(self._executor, self._loop, *args, **kwargs)

    async def disconnect(self):
        return await self.run_in_executor(self._client.disconnect)

    async def execute(self, *args, **kwargs):
        return await self.run_in_executor(self._client.execute, *args,
                                          **kwargs)

    async def execute_with_progress(self, query, with_column_types=False,
                                    external_tables=None, query_id=None,
                                    settings=None):
        await self.run_in_executor(self._client.connection.force_connect)

        return await self.process_ordinary_query_with_progress(
            query, with_column_types=with_column_types,
            external_tables=external_tables,
            query_id=query_id, settings=settings
        )

    async def process_ordinary_query_with_progress(
            self, query, with_column_types=False, external_tables=None,
            query_id=None, settings=None):
        await self.run_in_executor(
            self._client.connection.send_query, query,
            query_id=query_id, settings=settings
        )
        await self.run_in_executor(
            self._client.connection.send_external_tables, external_tables
        )

        return await self.receive_result(
            with_column_types=with_column_types, progress=True
        )

    async def receive_result(self, with_column_types=False, progress=False):
        result = QueryResult(with_column_types=with_column_types)

        if progress:
            return Progress(result, self)

        else:
            await self.run_in_executor(self._client.receive_no_progress_result,
                                       result)
            return result.get_result()

    async def cancel(self, with_column_types=False):
        # TODO: Add warning if already cancelled.
        await self.run_in_executor(self._client.connection.send_cancel)
        # Client must still read until END_OF_STREAM packet.
        return await self.receive_result(with_column_types=with_column_types)
