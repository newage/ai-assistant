<?php

declare(strict_types=1);

namespace Mcp;

use Mcp\Log\RequestLogger;
use Psr\Log\LoggerInterface;
use Psr\Log\NullLogger;

/**
 * Minimal MCP (streamable HTTP, JSON responses only) JSON-RPC handler:
 * initialize, notifications/initialized, ping, tools/list, tools/call.
 */
final class McpHandler
{
    private const PROTOCOL_VERSION = '2025-03-26';

    public function __construct(private readonly Tools $tools)
    {
    }

    /** @return array<string, mixed>|null null means "no response body" (notification) */
    public function handle(mixed $message, ?LoggerInterface $log = null): ?array
    {
        if (!is_array($message) || ($message['jsonrpc'] ?? null) !== '2.0' || !isset($message['method'])) {
            return self::failure($message['id'] ?? null, -32600, 'Invalid Request');
        }

        $isNotification = !array_key_exists('id', $message);
        $id = $message['id'] ?? null;
        $params = is_array($message['params'] ?? null) ? $message['params'] : [];

        if ($isNotification) {
            return null;
        }

        return match ($message['method']) {
            'initialize' => self::success($id, [
                'protocolVersion' => self::PROTOCOL_VERSION,
                'capabilities' => ['tools' => ['listChanged' => false]],
                'serverInfo' => ['name' => 'demo-user-data', 'version' => '1.0.0'],
            ]),
            'ping' => self::success($id, new \stdClass()),
            'tools/list' => self::success($id, ['tools' => $this->tools->definitions()]),
            'tools/call' => $this->callTool($id, $params, $log ?? new NullLogger()),
            default => self::failure($id, -32601, 'Method not found'),
        };
    }

    /** @param array<string, mixed> $params */
    private function callTool(mixed $id, array $params, LoggerInterface $log): array
    {
        $name = $params['name'] ?? null;
        $arguments = is_array($params['arguments'] ?? null) ? $params['arguments'] : [];

        if (!is_string($name)) {
            return self::failure($id, -32602, 'Invalid params: name is required');
        }

        $started = hrtime(true);
        try {
            $result = $this->tools->call($name, $arguments);
        } catch (\PDOException $e) {
            throw $e; // let the transport drop the connection and report the DB as unavailable
        } catch (\Throwable $e) {
            $log->error('tool call failed', ['tool' => $name, 'exception' => $e]);

            return self::success($id, [
                'content' => [['type' => 'text', 'text' => 'Internal error while reading user data.']],
                'isError' => true,
            ]);
        }

        $durationMs = round((hrtime(true) - $started) / 1e6, 1);
        $log->info('tool call', ['tool' => $name, 'status' => ($result['isError'] ?? false) ? 'error' : 'ok', 'duration_ms' => $durationMs]);
        $log->debug('tool call content', [
            'tool' => $name,
            'arguments' => RequestLogger::truncate($arguments),
            'result' => RequestLogger::truncate($result['content'][0]['text'] ?? ''),
        ]);

        return $result === null
            ? self::failure($id, -32602, "Unknown tool: $name")
            : self::success($id, $result);
    }

    private static function success(mixed $id, mixed $result): array
    {
        return ['jsonrpc' => '2.0', 'id' => $id, 'result' => $result];
    }

    private static function failure(mixed $id, int $code, string $message): array
    {
        return ['jsonrpc' => '2.0', 'id' => $id, 'error' => ['code' => $code, 'message' => $message]];
    }
}
