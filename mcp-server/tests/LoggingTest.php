<?php

declare(strict_types=1);

namespace Mcp\Tests;

use Mcp\Log\RequestLogger;
use PHPUnit\Framework\Attributes\DataProvider;

final class LoggingTest extends McpTestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        putenv('LOG_ID=vadym');
        putenv('ENVIRONMENT=local');
    }

    protected function tearDown(): void
    {
        putenv('LOG_ID');
        putenv('ENVIRONMENT');
    }

    /** @return array{0: \Monolog\Logger, 1: resource} */
    private function logger(?string $id, ?string $debug = null): array
    {
        $stream = fopen('php://memory', 'w+');

        return [RequestLogger::create($id, $debug, $stream), $stream];
    }

    /** @param resource $stream @return list<array<string, mixed>> */
    private function lines($stream): array
    {
        rewind($stream);
        $lines = array_filter(explode("\n", stream_get_contents($stream)));

        return array_values(array_map(static fn (string $l) => json_decode($l, true, 512, JSON_THROW_ON_ERROR), $lines));
    }

    private function callWithLogger(\Monolog\Logger $log): void
    {
        $this->handler->handle([
            'jsonrpc' => '2.0', 'id' => 1, 'method' => 'tools/call',
            'params' => ['name' => 'find_user_profile', 'arguments' => ['email' => 'olena1@example.com']],
        ], $log);
    }

    public function testRecordHasAllRequiredFields(): void
    {
        [$log, $stream] = $this->logger('abc123');
        $log->warning('hello', ['k' => 'v']);

        $line = $this->lines($stream)[0];
        foreach (['priority', 'service', 'short_message', 'x-request-id', 'extra', 'timestamp', 'log_id', 'environment'] as $key) {
            $this->assertArrayHasKey($key, $line);
        }
        $this->assertSame('WARNING', $line['priority']);
        $this->assertSame('mcp-server', $line['service']);
        $this->assertSame(['k' => 'v'], $line['extra']);
        $this->assertSame('vadym', $line['log_id']);
        $this->assertSame('local', $line['environment']);
        $this->assertMatchesRegularExpression('/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}\+00:00$/', $line['timestamp']);
    }

    public function testEmptyExtraIsEmptyList(): void
    {
        [$log, $stream] = $this->logger('abc123');
        $log->info('x');

        $this->assertSame([], $this->lines($stream)[0]['extra']);
    }

    public function testRequestIdOnEveryLineOfTheRequest(): void
    {
        [$log, $stream] = $this->logger('abc123');
        $this->callWithLogger($log);

        $lines = $this->lines($stream);
        $this->assertNotEmpty($lines);
        $this->assertSame(['abc123'], array_values(array_unique(array_column($lines, 'x-request-id'))));
    }

    #[DataProvider('badIds')]
    public function testMissingOrMalformedIdFallsBackToDash(?string $id): void
    {
        [$log, $stream] = $this->logger($id);
        $log->info('x');

        $this->assertSame('-', $this->lines($stream)[0]['x-request-id']);
    }

    public static function badIds(): array
    {
        return [[null], [''], ["has space"], ["new\nline"], [str_repeat('x', 65)]];
    }

    public function testInfoLogsMetadataOnly(): void
    {
        putenv('ENVIRONMENT=prod');
        [$log, $stream] = $this->logger('abc123');
        $this->callWithLogger($log);

        $raw = json_encode($this->lines($stream));
        $this->assertStringContainsString('find_user_profile', $raw);
        $this->assertStringContainsString('duration_ms', $raw);
        $this->assertStringNotContainsString('olena1@example.com', $raw);
        $this->assertNotContains('DEBUG', array_column($this->lines($stream), 'priority'));
    }

    public function testDebugLogsArgumentsAndResult(): void
    {
        [$log, $stream] = $this->logger('abc123');
        $this->callWithLogger($log);

        $debug = array_values(array_filter($this->lines($stream), static fn ($l) => $l['priority'] === 'DEBUG'));
        $this->assertCount(1, $debug);
        $this->assertStringContainsString('olena1@example.com', $debug[0]['extra']['arguments']);
        $this->assertStringContainsString('olena1@example.com', $debug[0]['extra']['result']);
    }

    public function testDebugHeaderEnablesDebugInProduction(): void
    {
        putenv('ENVIRONMENT=prod');
        [$log, $stream] = $this->logger('abc123', 'true');
        $this->callWithLogger($log);

        $this->assertContains('DEBUG', array_column($this->lines($stream), 'priority'));
    }

    public function testFalseHeaderDoesNotChangeTheEnvironmentRule(): void
    {
        $this->assertTrue(RequestLogger::debugEnabled('false', 'local'));
        $this->assertFalse(RequestLogger::debugEnabled('false', 'prod'));
        $this->assertFalse(RequestLogger::debugEnabled(null, 'prod'));
        $this->assertTrue(RequestLogger::debugEnabled('true', 'prod'));
    }

    public function testContentIsTruncated(): void
    {
        $this->assertSame(501, mb_strlen(RequestLogger::truncate(str_repeat('я', 2000))));
    }
}
