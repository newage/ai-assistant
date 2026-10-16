<?php

declare(strict_types=1);

use Mcp\McpHandler;
use Mcp\Tools;
use Mcp\UserRepository;
use Swoole\Http\Request;
use Swoole\Http\Response;
use Swoole\Http\Server;

require __DIR__ . '/vendor/autoload.php';

$dsn = sprintf(
    'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
    getenv('DB_HOST') ?: 'mysql',
    getenv('DB_PORT') ?: '3306',
    getenv('DB_NAME') ?: 'demo'
);

$server = new Server('0.0.0.0', (int) (getenv('MCP_PORT') ?: 9501));
$server->set(['worker_num' => (int) (getenv('MCP_WORKERS') ?: 2)]);

/** One PDO connection per worker, reconnecting lazily after a failure. */
$pdo = null;
$handler = null;

$connect = static function () use ($dsn, &$pdo, &$handler): void {
    $pdo = new PDO($dsn, getenv('DB_USER') ?: 'readonly', getenv('DB_PASSWORD') ?: '', [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);
    $handler = new McpHandler(new Tools(new UserRepository($pdo)));
};

$json = static function (Response $res, int $status, ?array $body): void {
    $res->status($status);
    $res->header('Content-Type', 'application/json');
    $res->end($body === null ? '' : json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
};

$server->on('request', static function (Request $req, Response $res) use (&$handler, &$pdo, $connect, $json): void {
    $path = parse_url($req->server['request_uri'] ?? '/', PHP_URL_PATH);
    $method = $req->server['request_method'] ?? 'GET';

    if ($path === '/health') {
        $json($res, 200, ['status' => 'ok']);
        return;
    }

    if ($path !== '/mcp') {
        $json($res, 404, ['error' => 'not found']);
        return;
    }

    if ($method !== 'POST') {
        $res->header('Allow', 'POST');
        $json($res, 405, ['error' => 'method not allowed']);
        return;
    }

    $message = json_decode($req->rawContent() ?: '', true);
    if ($message === null) {
        $json($res, 400, ['jsonrpc' => '2.0', 'id' => null, 'error' => ['code' => -32700, 'message' => 'Parse error']]);
        return;
    }

    try {
        if ($handler === null) {
            $connect();
        }
        $isBatch = array_is_list($message) && $message !== [];
        $responses = [];
        foreach ($isBatch ? $message : [$message] as $item) {
            $out = $handler->handle($item);
            if ($out !== null) {
                $responses[] = $out;
            }
        }
    } catch (\PDOException) {
        $handler = null;
        $pdo = null;
        $json($res, 503, ['jsonrpc' => '2.0', 'id' => null, 'error' => ['code' => -32000, 'message' => 'Database unavailable']]);
        return;
    }

    if ($responses === []) {
        $res->status(202);
        $res->end();
        return;
    }
    $json($res, 200, $isBatch ? $responses : $responses[0]);
});

$server->start();
